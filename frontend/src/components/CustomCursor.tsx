import { useEffect, useState } from "react";

type CursorState = "default" | "pointer" | "text";

/**
 * Custom brutalist cursor with circle and coral shadow.
 * Shows a trailing effect, expands on clickable elements, and changes to text cursor on inputs.
 */
export function CustomCursor() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [cursorState, setCursorState] = useState<CursorState>("default");
  const [isVisible, setIsVisible] = useState(false);
  const [isClicking, setIsClicking] = useState(false);

  useEffect(() => {
    // Only show custom cursor on devices with fine pointer (mouse)
    const hasFineMouse = window.matchMedia("(pointer: fine)").matches;
    if (!hasFineMouse) return;

    const updatePosition = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
      setIsVisible(true);
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

    const handleMouseDown = () => setIsClicking(true);
    const handleMouseUp = () => setIsClicking(false);
    const handleMouseLeave = () => setIsVisible(false);
    const handleMouseEnter = () => setIsVisible(true);

    document.addEventListener("mousemove", updatePosition);
    document.addEventListener("mouseover", updateCursorState);
    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("mouseup", handleMouseUp);
    document.documentElement.addEventListener("mouseleave", handleMouseLeave);
    document.documentElement.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      document.removeEventListener("mousemove", updatePosition);
      document.removeEventListener("mouseover", updateCursorState);
      document.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("mouseup", handleMouseUp);
      document.documentElement.removeEventListener("mouseleave", handleMouseLeave);
      document.documentElement.removeEventListener("mouseenter", handleMouseEnter);
    };
  }, []);

  // Don't render on touch devices
  if (typeof window !== "undefined" && !window.matchMedia("(pointer: fine)").matches) {
    return null;
  }

  // Get cursor size based on state
  const getSize = () => {
    switch (cursorState) {
      case "pointer":
        return { width: 40, height: 40 };
      case "text":
        return { width: 3, height: 24 };
      default:
        return { width: 12, height: 12 };
    }
  };

  const size = getSize();
  const isText = cursorState === "text";

  return (
    <>
      {/* Main cursor */}
      <div
        className="fixed pointer-events-none z-[9999] mix-blend-difference"
        style={{
          left: position.x,
          top: position.y,
          opacity: isVisible ? 1 : 0,
          transition: "opacity 0.15s ease, transform 0.1s ease",
          transform: `translate(-50%, -50%) scale(${isClicking ? 0.8 : 1})`,
        }}
      >
        {/* Circle cursor (or line for text) */}
        <div
          className={`bg-white transition-all duration-150 ease-out ${isText ? "" : "rounded-full"}`}
          style={{
            width: size.width,
            height: size.height,
            boxShadow: isText ? "1px 1px 0 #F3787A" : "2px 2px 0 #F3787A",
          }}
        />
      </div>

      {/* Trailing cursor (coral shadow) */}
      <div
        className="fixed pointer-events-none z-[9998]"
        style={{
          left: position.x,
          top: position.y,
          opacity: isVisible ? 0.5 : 0,
          transition: "left 0.15s ease-out, top 0.15s ease-out, opacity 0.15s ease, transform 0.15s ease",
          transform: `translate(-50%, -50%) scale(${isClicking ? 0.6 : 1})`,
        }}
      >
        <div
          className={`bg-[#F3787A] transition-all duration-200 ease-out ${isText ? "" : "rounded-full"}`}
          style={{
            width: size.width,
            height: size.height,
          }}
        />
      </div>
    </>
  );
}
