'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Users,
  UserCheck,
  Briefcase,
  TrendingUp,
  ChevronRight,
  Network,
} from 'lucide-react';

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubItem,
  SidebarMenuSubButton,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';

const navigation = [
  {
    title: 'Positions',
    url: '/positions',
    icon: Briefcase,
    disabled: false,
  },
  {
    title: 'Candidates',
    url: '/candidates',
    icon: TrendingUp,
    disabled: false,
  },
];

export function AppSidebar() {
  const pathname = usePathname();
  const { state } = useSidebar();
  const [teamsSubmenuOpen, setTeamsSubmenuOpen] = useState(
    pathname.startsWith('/teams') || pathname.startsWith('/interviewers')
  );

  const isActive = (url: string) => {
    if (url === '/') {
      return pathname === '/';
    }
    return pathname.startsWith(url);
  };

  const isTeamsActive = pathname.startsWith('/teams') && !pathname.startsWith('/interviewers');
  const isInterviewersActive = pathname.startsWith('/interviewers');
  const isCollapsed = state === 'collapsed';

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {/* Dashboard */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={isActive('/')}
                  tooltip="Dashboard"
                >
                  <Link href="/">
                    <Home />
                    <span>Dashboard</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              
              {/* Teams with Interviewers submenu */}
              <SidebarMenuItem>
                <Collapsible 
                  open={teamsSubmenuOpen} 
                  onOpenChange={setTeamsSubmenuOpen}
                  className="group/collapsible w-full"
                >
                  <div className="flex items-center w-full">
                    <SidebarMenuButton
                      asChild
                      isActive={isTeamsActive || isInterviewersActive}
                      tooltip="Teams"
                      className="flex-1"
                    >
                      <Link href="/teams">
                        <Users />
                        <span>Teams</span>
                      </Link>
                    </SidebarMenuButton>
                    {!isCollapsed && (
                      <CollapsibleTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 p-0 mr-1 shrink-0"
                        >
                          <ChevronRight className="h-4 w-4 transition-transform duration-200 group-data-[state=open]/collapsible:rotate-90" />
                        </Button>
                      </CollapsibleTrigger>
                    )}
                  </div>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          asChild
                          isActive={isInterviewersActive}
                        >
                          <Link href="/interviewers">
                            <UserCheck />
                            <span>Interviewers</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </Collapsible>
              </SidebarMenuItem>

              {/* Other navigation items */}
              {navigation.map((item) => (
                <SidebarMenuItem key={item.title}>
                  {item.disabled ? (
                    <SidebarMenuButton disabled tooltip={item.title}>
                      <item.icon />
                      <span>{item.title}</span>
                    </SidebarMenuButton>
                  ) : (
                    <SidebarMenuButton
                      asChild
                      isActive={isActive(item.url)}
                      tooltip={item.title}
                    >
                      <Link href={item.url}>
                        <item.icon />
                        <span>{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  )}
                </SidebarMenuItem>
              ))}

              {/* Graph - moved to bottom */}
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={isActive('/graph')}
                  tooltip="Graph"
                >
                  <Link href="/graph">
                    <Network />
                    <span>Graph</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}

