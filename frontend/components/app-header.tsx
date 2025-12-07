'use client';

import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from '@/components/ui/navigation-menu';
import { SidebarTrigger } from '@/components/ui/sidebar';

export function AppHeader() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center px-4">
        <SidebarTrigger className="mr-2" />
        <div className="mr-4">
          <span className="font-semibold">Grok Recruiting</span>
        </div>
        <div className="flex flex-1 items-center justify-end">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">Company:</span>
            <span className="font-medium text-foreground">xAI</span>
          </div>
        </div>
      </div>
    </header>
  );
}

