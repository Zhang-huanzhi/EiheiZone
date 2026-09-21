"use client";

import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

const SLOW_NAVIGATION_DELAY = 1200;

export function NavigationProgress() {
  const pathname = usePathname();
  const [pending, setPending] = useState(false);
  const [slow, setSlow] = useState(false);
  const startedPath = useRef(pathname);
  const slowTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearSlowTimer = useCallback(() => {
    if (slowTimer.current !== null) {
      clearTimeout(slowTimer.current);
      slowTimer.current = null;
    }
  }, []);

  const finishNavigation = useCallback(() => {
    clearSlowTimer();
    setSlow(false);
    setPending(false);
  }, [clearSlowTimer]);

  const startNavigation = useCallback(() => {
    if (pending) return;

    startedPath.current = pathname;
    setPending(true);
    clearSlowTimer();
    slowTimer.current = setTimeout(() => setSlow(true), SLOW_NAVIGATION_DELAY);
  }, [clearSlowTimer, pathname, pending]);

  useEffect(() => {
    if (pending && pathname !== startedPath.current) {
      finishNavigation();
    }
  }, [finishNavigation, pathname, pending]);

  useEffect(() => {
    function handleDocumentClick(event: MouseEvent) {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const anchor = target.closest("a");
      if (!(anchor instanceof HTMLAnchorElement)) return;
      if (!isNavigableClick(anchor, event)) return;

      startNavigation();
    }

    document.addEventListener("click", handleDocumentClick, true);
    return () => document.removeEventListener("click", handleDocumentClick, true);
  }, [clearSlowTimer, startNavigation]);

  useEffect(() => () => clearSlowTimer(), [clearSlowTimer]);

  if (!pending) return null;

  return (
    <div className="pointer-events-none fixed inset-x-0 top-0 z-[100]" aria-live="polite">
      <div aria-hidden="true" className="h-1 w-full overflow-hidden bg-primary/15">
        <div className="navigation-progress-bar h-full w-1/3 bg-primary" />
      </div>
      {slow ? (
        <p className="mx-auto mt-2 w-fit rounded-md border border-border bg-background px-3 py-1.5 text-xs text-muted-foreground shadow-sm">
          网络较慢，仍在加载...
        </p>
      ) : null}
    </div>
  );
}

function isNavigableClick(
  anchor: HTMLAnchorElement,
  event: MouseEvent,
): boolean {
  if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    return false;
  }
  if (anchor.target && anchor.target !== "_self") return false;
  if (anchor.hasAttribute("download")) return false;

  const url = new URL(anchor.href, window.location.href);
  return url.origin === window.location.origin &&
    (url.pathname !== window.location.pathname || url.search !== window.location.search);
}
