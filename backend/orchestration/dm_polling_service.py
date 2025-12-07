"""
dm_polling_service.py - Async background service for polling DM responses

This service runs continuously in the background, polling X API for new DM responses
and automatically processing them through the pipeline.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from backend.integrations.x_dm_service import XDMService
from backend.orchestration.dm_screening_service import DMScreeningService
from backend.database.postgres_client import PostgresClient
from backend.orchestration.company_context import get_company_context

logger = logging.getLogger(__name__)


class DMPollingService:
    """
    Async background service that continuously polls for DM responses.
    
    Runs in the background, checking for new DM messages every 30 seconds
    and automatically processing them through the pipeline.
    """
    
    def __init__(
        self,
        dm_service: Optional[XDMService] = None,
        screening_service: Optional[DMScreeningService] = None,
        postgres: Optional[PostgresClient] = None,
        poll_interval: int = 5
    ):
        """
        Initialize DM polling service.
        
        Args:
            dm_service: X DM service instance
            screening_service: DM screening service instance
            postgres: PostgreSQL client instance
            poll_interval: Seconds between polls (default: 5)
        """
        self.dm_service = dm_service
        self.screening_service = screening_service or DMScreeningService(dm_service=dm_service, postgres=postgres)
        self.postgres = postgres or PostgresClient()
        self.company_context = get_company_context()
        self.poll_interval = poll_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the background polling service."""
        if self.is_running:
            logger.warning("DM polling service is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"DM polling service started (polling every {self.poll_interval} seconds)")
    
    async def stop(self):
        """Stop the background polling service."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("DM polling service stopped")
    
    async def _poll_loop(self):
        """Main polling loop."""
        logger.info(f"🔄 POLLING LOOP: Starting polling loop (interval: {self.poll_interval}s)")
        while self.is_running:
            try:
                logger.debug(f"🔄 POLLING LOOP: Starting poll cycle")
                await self._poll_all_conversations()
                logger.debug(f"🔄 POLLING LOOP: Completed poll cycle")
            except Exception as e:
                logger.error(f"❌ POLLING LOOP ERROR: Error in polling loop: {e}", exc_info=True)
            
            # Wait before next poll
            logger.debug(f"🔄 POLLING LOOP: Waiting {self.poll_interval} seconds before next poll")
            await asyncio.sleep(self.poll_interval)
    
    async def _poll_all_conversations(self):
        """Poll all active DM conversations for new messages."""
        company_id = self.company_context.get_company_id()
        
        # Get all active conversations that need polling
        # Poll conversations that haven't been polled in the last 10 seconds
        # (Since we poll every 5 seconds, this ensures we check conversations frequently)
        # Use PostgreSQL's NOW() to avoid timezone issues
        logger.info(
            f"🔍 POLLING: Checking for conversations to poll (company: {company_id})"
        )
        
        # First, let's see ALL active conversations to debug
        all_active = self.postgres.execute_query(
            """
            SELECT 
                id, candidate_id, position_id, x_conversation_id, 
                x_participant_id, x_participant_handle, last_message_id, last_polled_at,
                EXTRACT(EPOCH FROM (NOW() - last_polled_at)) as seconds_ago
            FROM dm_conversations
            WHERE company_id = %s AND status = 'active'
            ORDER BY last_polled_at ASC NULLS FIRST
            """,
            (company_id,)
        )
        
        if all_active:
            logger.info(f"🔍 POLLING: All active conversations ({len(all_active)}):")
            for conv in all_active:
                last_polled = conv.get('last_polled_at')
                seconds_ago = conv.get('seconds_ago', 0)
                logger.info(
                    f"  - {conv.get('x_conversation_id')}: "
                    f"last_polled={last_polled}, "
                    f"seconds_ago={seconds_ago:.0f}s"
                )
        
        # Use PostgreSQL's NOW() - INTERVAL to avoid timezone issues
        conversations = self.postgres.execute_query(
            """
            SELECT 
                id, candidate_id, position_id, x_conversation_id, 
                x_participant_id, x_participant_handle, last_message_id, last_polled_at
            FROM dm_conversations
            WHERE company_id = %s
              AND status = 'active'
              AND (last_polled_at IS NULL OR last_polled_at < NOW() - INTERVAL '10 seconds')
            ORDER BY last_polled_at ASC NULLS FIRST
            LIMIT 50
            """,
            (company_id,)
        )
        
        if not conversations:
            logger.info(f"🔍 POLLING: No conversations found to poll (company: {company_id}, cutoff: 10 seconds ago)")
            # Log total count of active conversations and their last_polled_at times for debugging
            total_active = self.postgres.execute_one(
                """
                SELECT COUNT(*) as count
                FROM dm_conversations
                WHERE company_id = %s AND status = 'active'
                """,
                (company_id,)
            )
            if total_active:
                count = total_active.get('count', 0)
                logger.info(f"🔍 POLLING: Total active conversations in DB: {count}")
                
                # Show why conversations aren't being polled
                if count > 0:
                    recent_convs = self.postgres.execute_query(
                        """
                        SELECT 
                            x_conversation_id, candidate_id, position_id, 
                            last_polled_at, 
                            EXTRACT(EPOCH FROM (NOW() - last_polled_at)) as seconds_since_poll
                        FROM dm_conversations
                        WHERE company_id = %s AND status = 'active'
                        ORDER BY last_polled_at DESC NULLS FIRST
                        LIMIT 5
                        """,
                        (company_id,)
                    )
                    if recent_convs:
                        logger.info(f"🔍 POLLING: Recent conversations status:")
                        for conv in recent_convs:
                            last_polled = conv.get('last_polled_at')
                            seconds_ago = conv.get('seconds_since_poll')
                            if last_polled:
                                logger.info(
                                    f"  - Conversation {conv.get('x_conversation_id')}: "
                                    f"last polled {seconds_ago:.0f}s ago at {last_polled}"
                                )
                            else:
                                logger.info(
                                    f"  - Conversation {conv.get('x_conversation_id')}: "
                                    f"never polled (NULL)"
                                )
            return
        
        logger.info(f"🔍 POLLING: Found {len(conversations)} conversation(s) to poll")
        
        for idx, conv in enumerate(conversations, 1):
            try:
                logger.debug(
                    f"🔍 POLLING: [{idx}/{len(conversations)}] Polling conversation "
                    f"{conv['x_conversation_id']} for candidate {conv['candidate_id']}"
                )
                await self._poll_conversation(conv)
                # Small delay between conversations to avoid rate limits
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"❌ POLLING ERROR: Error polling conversation {conv['x_conversation_id']}: {e}")
                continue
    
    async def _poll_conversation(self, conversation: Dict[str, Any]):
        """Poll a single conversation for new messages."""
        conversation_id = conversation['x_conversation_id']
        candidate_id = conversation['candidate_id']
        position_id = conversation['position_id']
        last_message_id = conversation.get('last_message_id')
        last_polled_at = conversation.get('last_polled_at')
        
        logger.debug(
            f"🔍 POLLING CONVERSATION: {conversation_id} "
            f"(candidate: {candidate_id}, position: {position_id}, "
            f"last_message: {last_message_id}, last_polled: {last_polled_at})"
        )
        
        try:
            # Get conversation from X API
            if not self.dm_service:
                logger.warning("⚠️ POLLING: DM service not available, skipping poll")
                return
            
            logger.debug(f"🔍 POLLING CONVERSATION: Fetching conversation {conversation_id} from X API")
            conv_data = await self.dm_service.get_dm_conversation(conversation_id)
            
            if not conv_data:
                logger.warning(f"⚠️ POLLING: Could not retrieve conversation {conversation_id}")
                return
            
            logger.debug(f"🔍 POLLING CONVERSATION: Retrieved conversation data from X API")
            
            # Extract messages from conversation data
            # X API returns messages in different possible structures
            messages = []
            if 'dm_events' in conv_data:
                messages = conv_data['dm_events']
            elif 'events' in conv_data:
                messages = conv_data['events']
            elif isinstance(conv_data, list):
                messages = conv_data
            elif 'data' in conv_data and 'dm_events' in conv_data['data']:
                messages = conv_data['data']['dm_events']
            
            logger.info(f"🔍 POLLING CONVERSATION: Found {len(messages)} total message(s) in conversation")
            
            if not messages:
                logger.info(f"🔍 POLLING CONVERSATION: No messages found, updating last_polled_at")
                # Update last_polled_at even if no messages
                self._update_last_polled(conversation['id'])
                return
            
            # Log all messages for debugging
            logger.info(f"🔍 POLLING CONVERSATION: Analyzing {len(messages)} message(s):")
            for idx, msg in enumerate(messages, 1):
                msg_id = msg.get('id')
                sender_id = msg.get('sender_id')
                text_preview = msg.get('text', '')[:50] if msg.get('text') else '(no text)'
                created_at = msg.get('created_at', 'unknown')
                logger.info(
                    f"  [{idx}] Message {msg_id}: sender={sender_id}, "
                    f"text='{text_preview}...', created={created_at}"
                )
            
            # Get authenticated user ID to filter out our own messages
            from backend.integrations.x_dm_service import XDMService
            oauth2_token = await self.dm_service._get_oauth2_access_token(force_refresh=True)
            authenticated_user_id = await self.dm_service._get_authenticated_user_id(oauth2_token)
            
            logger.info(
                f"🔍 POLLING CONVERSATION: Authenticated user ID: {authenticated_user_id}, "
                f"Participant (candidate) ID: {conversation.get('x_participant_id')}, "
                f"Last processed message ID: {last_message_id}"
            )
            
            # Filter for new messages (after last_message_id)
            new_messages = []
            participant_id = conversation.get('x_participant_id')
            
            if last_message_id:
                logger.info(f"🔍 POLLING CONVERSATION: Looking for messages after {last_message_id}")
                # Find messages after the last one we processed
                for msg in messages:
                    msg_id = msg.get('id')
                    sender_id = msg.get('sender_id')
                    
                    # Skip if this is the last message we processed
                    if msg_id == last_message_id:
                        logger.debug(f"  Skipping message {msg_id} (already processed)")
                        continue
                    
                    # Check if this message is from the candidate (not from us)
                    if sender_id == participant_id:
                        logger.info(
                            f"  ✅ Found new message from candidate: {msg_id} "
                            f"(sender: {sender_id}, text: '{msg.get('text', '')[:50]}...')"
                        )
                        new_messages.append(msg)
                    elif sender_id == authenticated_user_id:
                        logger.debug(f"  Skipping message {msg_id} (from us, sender: {sender_id})")
                    else:
                        logger.warning(
                            f"  ⚠️ Unknown sender for message {msg_id}: {sender_id} "
                            f"(expected candidate: {participant_id} or us: {authenticated_user_id})"
                        )
            else:
                logger.info(f"🔍 POLLING CONVERSATION: First time polling - checking all messages from candidate")
                # First time polling - get all messages from candidate
                for msg in messages:
                    msg_id = msg.get('id')
                    sender_id = msg.get('sender_id')
                    
                    if sender_id == participant_id:
                        logger.info(
                            f"  ✅ Found message from candidate: {msg_id} "
                            f"(text: '{msg.get('text', '')[:50]}...')"
                        )
                        new_messages.append(msg)
                    elif sender_id == authenticated_user_id:
                        logger.debug(f"  Skipping message {msg_id} (from us)")
                    else:
                        logger.warning(f"  ⚠️ Unknown sender: {sender_id}")
            
            # Process new messages
            if new_messages:
                logger.info(
                    f"📥 DATA INTAKE: Found {len(new_messages)} new message(s) in conversation {conversation_id} "
                    f"for candidate {candidate_id}, position {position_id}"
                )
                
                # Process the most recent message (candidates usually respond once)
                latest_message = new_messages[-1]
                message_text = latest_message.get('text', '')
                message_id = latest_message.get('id')
                created_at = latest_message.get('created_at', 'unknown')
                
                logger.info(
                    f"📥 DATA INTAKE: Processing message {message_id} "
                    f"(created: {created_at}, length: {len(message_text)} chars)"
                )
                logger.debug(f"📥 DATA INTAKE: Message content preview: {message_text[:200]}...")
                
                if message_text:
                    await self._process_message(
                        candidate_id=candidate_id,
                        position_id=position_id,
                        message_text=message_text,
                        message_id=message_id,
                        conversation_id=conversation['id']
                    )
                
                # Update last_message_id
                self._update_last_message_id(conversation['id'], message_id)
            else:
                logger.info(
                    f"🔍 POLLING CONVERSATION: No new messages from candidate found. "
                    f"Total messages: {len(messages)}, "
                    f"Last processed: {last_message_id or 'none'}, "
                    f"Participant ID: {participant_id}"
                )
            
            # Update last_polled_at
            self._update_last_polled(conversation['id'])
            
        except Exception as e:
            logger.error(f"Error polling conversation {conversation_id}: {e}", exc_info=True)
    
    async def _process_message(
        self,
        candidate_id: str,
        position_id: str,
        message_text: str,
        message_id: str,
        conversation_id: int
    ):
        """Process a new DM message from a candidate."""
        try:
            logger.info(
                f"🔄 PROCESSING: Starting DM response processing for candidate {candidate_id} "
                f"position {position_id}, message {message_id}"
            )
            
            # Process the DM response through screening service
            logger.info(f"🔄 PROCESSING: Extracting and categorizing data from message...")
            try:
                result = await self.screening_service.process_dm_response(
                    candidate_id=candidate_id,
                    position_id=position_id,
                    dm_message_text=message_text
                )
                logger.info(f"🔄 PROCESSING: process_dm_response completed successfully")
            except Exception as process_error:
                logger.error(
                    f"❌ ERROR: process_dm_response failed: {process_error}",
                    exc_info=True
                )
                raise
            
            if not result:
                logger.error(f"❌ ERROR: process_dm_response returned None or empty result")
                return
            
            # Log extracted data and categorization
            extracted_fields = result.get('extracted_fields', {})
            screening_responses = result.get('screening_responses', {})
            screening_score = result.get('screening_score', 0)
            new_stage = result.get('new_stage', 'unknown')
            
            logger.info(
                f"✅ CATEGORIZATION: Processed DM response for candidate {candidate_id}: "
                f"score={screening_score:.2f}, stage={new_stage}"
            )
            
            if extracted_fields:
                logger.info(
                    f"📊 DATA EXTRACTION: Extracted fields: {list(extracted_fields.keys())} - "
                    f"{extracted_fields}"
                )
            else:
                logger.info(f"📊 DATA EXTRACTION: No fields extracted from message")
            
            if screening_responses:
                logger.info(
                    f"📊 SCREENING DATA: Screening responses: {list(screening_responses.keys())} - "
                    f"{screening_responses}"
                )
            
            # Log the processing result
            try:
                self._log_message_processing(
                    conversation_id=conversation_id,
                    message_id=message_id,
                    message_text=message_text,
                    result=result
                )
                logger.info(f"✅ LOGGING: Message processing logged to database")
            except Exception as log_error:
                logger.error(f"❌ ERROR: Failed to log message processing: {log_error}", exc_info=True)
            
            # Generate and send appropriate reply based on the response
            logger.info(f"💬 REPLY: Generating reply based on screening results...")
            try:
                await self._send_reply(
                    candidate_id=candidate_id,
                    position_id=position_id,
                    message_text=message_text,
                    result=result,
                    conversation_id=conversation_id
                )
                logger.info(f"✅ REPLY: Reply process completed")
            except Exception as reply_error:
                logger.error(f"❌ ERROR: Failed to send reply: {reply_error}", exc_info=True)
                # Don't raise - we still want to process the message even if reply fails
            
        except Exception as e:
            logger.error(f"❌ ERROR: Error processing message: {e}", exc_info=True)
    
    async def _send_reply(
        self,
        candidate_id: str,
        position_id: str,
        message_text: str,
        result: Dict[str, Any],
        conversation_id: int
    ):
        """Generate and send an appropriate reply to the candidate's DM."""
        try:
            # Get conversation details
            conv = self.postgres.execute_one(
                """
                SELECT x_conversation_id, x_participant_id, x_participant_handle
                FROM dm_conversations
                WHERE id = %s
                """,
                (conversation_id,)
            )
            
            if not conv or not self.dm_service:
                logger.warning(f"💬 REPLY: Cannot send reply - missing conversation or DM service")
                return
            
            x_conversation_id = conv.get('x_conversation_id')
            x_participant_id = conv.get('x_participant_id')
            x_participant_handle = conv.get('x_participant_handle', 'unknown')
            
            if not x_conversation_id:
                logger.warning(f"💬 REPLY: Cannot send reply - missing conversation ID")
                return
            
            logger.info(
                f"💬 REPLY: Generating reply for candidate {candidate_id} ({x_participant_handle}) "
                f"conversation {x_conversation_id}"
            )
            
            # Generate reply based on screening result
            reply_message = await self._generate_reply_message(
                candidate_id=candidate_id,
                position_id=position_id,
                message_text=message_text,
                result=result
            )
            
            if reply_message:
                logger.info(f"💬 REPLY: Generated reply message ({len(reply_message)} chars): {reply_message}")
                
                # Send reply to the conversation
                dm_result = await self.dm_service.send_dm_by_conversation_id(
                    conversation_id=x_conversation_id,
                    message=reply_message
                )
                
                if dm_result:
                    logger.info(
                        f"✅ REPLY SENT: Successfully sent reply to candidate {candidate_id} "
                        f"({x_participant_handle}) for position {position_id} "
                        f"in conversation {x_conversation_id}"
                    )
                else:
                    logger.warning(f"⚠️ REPLY FAILED: Failed to send reply to candidate {candidate_id}")
            else:
                logger.warning(f"⚠️ REPLY: No reply message generated for candidate {candidate_id}")
            
        except Exception as e:
            logger.error(f"❌ REPLY ERROR: Error sending reply: {e}", exc_info=True)
    
    async def _generate_reply_message(
        self,
        candidate_id: str,
        position_id: str,
        message_text: str,
        result: Dict[str, Any]
    ) -> Optional[str]:
        """Generate an appropriate reply message based on the candidate's response."""
        try:
            # Get candidate and position info
            candidate = self.postgres.execute_one(
                "SELECT name, x_handle FROM candidates WHERE id = %s",
                (candidate_id,)
            )
            position = self.postgres.execute_one(
                "SELECT title FROM positions WHERE id = %s",
                (position_id,)
            )
            
            candidate_name = candidate.get('name', 'there') if candidate else 'there'
            position_title = position.get('title', 'this position') if position else 'this position'
            
            screening_score = result.get('screening_score', 0)
            new_stage = result.get('new_stage', 'unknown')
            extracted_fields = result.get('extracted_fields', {})
            screening_responses = result.get('screening_responses', {})
            
            logger.info(
                f"💬 REPLY GENERATION: Creating reply for {candidate_name} "
                f"(score: {screening_score:.2f}, stage: {new_stage}, "
                f"extracted: {len(extracted_fields)} fields, "
                f"screening: {len(screening_responses)} responses)"
            )
            
            # Use Grok to generate a personalized, contextual reply
            from backend.integrations.grok_api import GrokAPIClient
            grok = GrokAPIClient()
            
            prompt = f"""Generate a friendly, professional reply to a candidate's DM response.

Candidate Name: {candidate_name}
Position: {position_title}
Screening Score: {screening_score:.2f}/1.0
New Stage: {new_stage}
Extracted Information: {extracted_fields}
Screening Responses: {screening_responses}

Candidate's Message: {message_text[:500]}

Generate a reply that:
1. Acknowledges their response
2. Thanks them for the information
3. If screening passed (score >= 0.5): Express interest and mention next steps (phone screen)
4. If screening failed (score < 0.5): Be polite and professional, thank them for their interest
5. If information is incomplete: Ask for missing critical information (but be brief)
6. Keep it warm, professional, and concise (2-3 sentences max)

Return ONLY the reply message text, no JSON, no markdown, just the message."""

            logger.debug(f"💬 REPLY GENERATION: Prompt sent to Grok (length: {len(prompt)} chars)")
            response = await grok._make_chat_request(prompt)
            
            # Extract message content
            if isinstance(response, dict):
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    content = response.get('content', response.get('text', response.get('message', '')))
                
                # Clean up markdown if present
                if "```" in content:
                    parts = content.split("```")
                    content = parts[-1].split("```")[0].strip() if len(parts) > 1 else content
                
                if isinstance(content, str) and content.strip():
                    logger.debug(f"💬 REPLY GENERATION: Generated reply from Grok: {content[:100]}...")
                    return content.strip()
            
            # Fallback to simple acknowledgment
            logger.info(f"💬 REPLY GENERATION: Using fallback reply (Grok response was empty)")
            if new_stage == 'dm_screening_passed':
                return f"Thanks {candidate_name}! We'd love to schedule a phone screen. Our team will reach out soon."
            elif new_stage == 'dm_screening_failed':
                return f"Thanks {candidate_name} for your interest in {position_title}. We'll keep your information on file."
            else:
                return f"Thanks {candidate_name}! We've received your information and will review it."
                
        except Exception as e:
            logger.error(f"❌ REPLY GENERATION ERROR: Error generating reply message: {e}", exc_info=True)
            return None
    
    def _update_last_polled(self, conversation_db_id: int):
        """Update last_polled_at timestamp."""
        self.postgres.execute_update(
            """
            UPDATE dm_conversations
            SET last_polled_at = NOW(), updated_at = NOW()
            WHERE id = %s
            """,
            (conversation_db_id,)
        )
    
    def _update_last_message_id(self, conversation_db_id: int, message_id: str):
        """Update last_message_id."""
        self.postgres.execute_update(
            """
            UPDATE dm_conversations
            SET last_message_id = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (message_id, conversation_db_id)
        )
    
    def _log_message_processing(
        self,
        conversation_id: int,
        message_id: str,
        message_text: str,
        result: Dict[str, Any]
    ):
        """Log message processing for monitoring."""
        logger.info(
            f"DM Message Processed | "
            f"Conversation: {conversation_id} | "
            f"Message ID: {message_id} | "
            f"Score: {result.get('screening_score', 0):.2f} | "
            f"Stage: {result.get('new_stage', 'unknown')} | "
            f"Preview: {message_text[:50]}..."
        )


# Global instance
_polling_service: Optional[DMPollingService] = None


def get_dm_polling_service() -> DMPollingService:
    """Get or create the global DM polling service instance."""
    global _polling_service
    if _polling_service is None:
        # Initialize XDMService for DM operations
        dm_service = XDMService()
        _polling_service = DMPollingService(dm_service=dm_service)
    return _polling_service


async def start_dm_polling():
    """Start the DM polling service (called on server startup)."""
    service = get_dm_polling_service()
    await service.start()


async def stop_dm_polling():
    """Stop the DM polling service (called on server shutdown)."""
    service = get_dm_polling_service()
    await service.stop()

