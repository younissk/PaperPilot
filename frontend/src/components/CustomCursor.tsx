import { useEffect, useRef, useState, useCallback } from "react";

type CursorState = "default" | "pointer" | "text";

/**
 * Custom brutalist cursor with circle and coral shadow.
 * Shows a trailing effect, expands on clickable elements, and changes to text cursor on inputs.
 * 
 * Performance optimized: Uses refs and direct DOM manipulation instead of React state
 * for position updates to avoid unnecessary re-renders on every mouse move.
 */
export function CustomCursor() {
  const mainCursorRef = useRef<HTMLDivElement>(null);
  const trailCursorRef = useRef<HTMLDivElement>(null);
  const mainInnerRef = useRef<HTMLDivElement>(null);
  const trailInnerRef = useRef<HTMLDivElement>(null);
  
  // Only state that needs re-renders (cursor type changes are infrequent)
  const [cursorState, setCursorState] = useState<CursorState>("default");
  
  // Use refs for frequently changing values to avoid re-renders
  const positionRef = useRef({ x: 0, y: 0 });
  const trailPositionRef = useRef({ x: 0, y: 0 });
  const isVisibleRef = useRef(false);
  const isClickingRef = useRef(false);
  const rafRef = useRef<number | null>(null);

  // Direct DOM update for cursor position (no React re-render)
  const updateCursorDOM = useCallback(() => {
    const main = mainCursorRef.current;
    const trail = trailCursorRef.current;
    
    if (main) {
      const { x, y } = positionRef.current;
      main.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${isClickingRef.current ? 0.8 : 1})`;
      main.style.opacity = isVisibleRef.current ? "1" : "0";
    }
    
    if (trail) {
      const { x, y } = trailPositionRef.current;
      trail.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${isClickingRef.current ? 0.6 : 1})`;
      trail.style.opacity = isVisibleRef.current ? "0.5" : "0";
    }
  }, []);

  // Smooth trail animation using lerp (linear interpolation)
  const animateTrail = useCallback(() => {
    const lerp = 0.15; // Smoothing factor (0-1, lower = smoother/slower)
    
    trailPositionRef.current.x += (positionRef.current.x - trailPositionRef.current.x) * lerp;
    trailPositionRef.current.y += (positionRef.current.y - trailPositionRef.current.y) * lerp;
    
    updateCursorDOM();
    rafRef.current = requestAnimationFrame(animateTrail);
  }, [updateCursorDOM]);

  useEffect(() => {
    // Only show custom cursor on devices with fine pointer (mouse)
    const hasFineMouse = window.matchMedia("(pointer: fine)").matches;
    if (!hasFineMouse) return;

    const handleMouseMove = (e: MouseEvent) => {
      positionRef.current.x = e.clientX;
      positionRef.current.y = e.clientY;
      isVisibleRef.current = true;
    };

    const updateCursorState = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      
      // Check if it's a text input
      const isTextInput =
        target.tagName === "INPUT" &&
        ["text", "email", "password", "search", "url", "tel", "number"].includes(
          (target as HTMLInputElement).type
        );
      const isTextArea = target.tagName === "TEXTAREA";
      const isContentEditable = target.isContentEditable;
      
      if (isTextInput || isTextArea || isContentEditable) {
        setCursorState("text");
        return;
      }

      // Check if it's clickable
      const isClickable =
        target.tagName === "A" ||
        target.tagName === "BUTTON" ||
        target.closest("a") ||
        target.closest("button") ||
        target.classList.contains("cursor-pointer") ||
        window.getComputedStyle(target).cursor === "pointer";
      
      setCursorState(isClickable ? "pointer" : "default");
    };

    const handleMouseDown = () => {
      isClickingRef.current = true;
    };
    
    const handleMouseUp = () => {
      isClickingRef.current = false;
    };
    
    const handleMouseLeave = () => {
      isVisibleRef.current = false;
    };
    
    const handleMouseEnter = () => {
      isVisibleRef.current = true;
    };

    // Start the animation loop
    rafRef.current = requestAnimationFrame(animateTrail);

    document.addEventListener("mousemove", handleMouseMove, { passive: true });
    document.addEventListener("mouseover", updateCursorState, { passive: true });
    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("mouseup", handleMouseUp);
    document.documentElement.addEventListener("mouseleave", handleMouseLeave);
    document.documentElement.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseover", updateCursorState);
      document.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("mouseup", handleMouseUp);
      document.documentElement.removeEventListener("mouseleave", handleMouseLeave);
      document.documentElement.removeEventListener("mouseenter", handleMouseEnter);
    };
  }, [animateTrail]);

  // Update cursor size when state changes (infrequent, OK to use effect)
  useEffect(() => {
    const mainInner = mainInnerRef.current;
    const trailInner = trailInnerRef.current;
    
    if (!mainInner || !trailInner) return;
    
    let width: number;
    let height: number;
    let isText = false;
    
    switch (cursorState) {
      case "pointer":
        width = 40;
        height = 40;
        break;
      case "text":
        width = 3;
        height = 24;
        isText = true;
        break;
      default:
        width = 12;
        height = 12;
    }
    
    mainInner.style.width = `${width}px`;
    mainInner.style.height = `${height}px`;
    mainInner.style.borderRadius = isText ? "0" : "50%";
    mainInner.style.boxShadow = isText ? "1px 1px 0 #F3787A" : "2px 2px 0 #F3787A";
    
    trailInner.style.width = `${width}px`;
    trailInner.style.height = `${height}px`;
    trailInner.style.borderRadius = isText ? "0" : "50%";
  }, [cursorState]);

  // Don't render on touch devices
  if (typeof window !== "undefined" && !window.matchMedia("(pointer: fine)").matches) {
    return null;
  }

  return (
    <>
      {/* Main cursor - position controlled via ref */}
      <div
        ref={mainCursorRef}
        className="fixed top-0 left-0 pointer-events-none z-[9999] mix-blend-difference will-change-transform"
        style={{ opacity: 0 }}
      >
        <div
          ref={mainInnerRef}
          className="bg-white rounded-full"
          style={{
            width: 12,
            height: 12,
            boxShadow: "2px 2px 0 #F3787A",
          }}
        />
      </div>

      {/* Trailing cursor - smooth follow via requestAnimationFrame */}
      <div
        ref={trailCursorRef}
        className="fixed top-0 left-0 pointer-events-none z-[9998] will-change-transform"
        style={{ opacity: 0 }}
      >
        <div
          ref={trailInnerRef}
          className="bg-[#F3787A] rounded-full"
          style={{
            width: 12,
            height: 12,
          }}
        />
      </div>
    </>
  );
}
