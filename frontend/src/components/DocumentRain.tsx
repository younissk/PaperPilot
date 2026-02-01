import { useEffect, useRef, useCallback } from "react";
import Matter from "matter-js";

interface DocumentRainProps {
  /** Maximum number of documents to spawn */
  maxDocuments?: number;
  /** Spawn interval in milliseconds */
  spawnInterval?: number;
  /** Document scale factor (1 = 36x46px based on 360x460 SVG) */
  scale?: number;
}

// SVG path data for the document icon (scaled down from 360x460 viewBox)
const DOC_WIDTH = 36;
const DOC_HEIGHT = 46;

// Light pastel colors for documents
const PASTEL_COLORS = [
  "#FFE5E5", // light pink
  "#E5F0FF", // light blue
  "#E5FFE5", // light green
  "#FFF5E5", // light peach
  "#F5E5FF", // light lavender
  "#E5FFFF", // light cyan
  "#FFFFE5", // light yellow
  "#FFE5F5", // light rose
  "#E5E5FF", // light periwinkle
  "#F0FFE5", // light mint
];

// Get a random pastel color
const getRandomPastelColor = (): string => {
  return PASTEL_COLORS[Math.floor(Math.random() * PASTEL_COLORS.length)];
};

// Poof particle interface
interface PoofParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  color: string;
  alpha: number;
  decay: number;
}

/**
 * Physics-based document rain animation using Matter.js.
 * Documents fall from the top and pile up at the bottom of the container.
 * Click on documents to make them "poof" away!
 */
export function DocumentRain({
  maxDocuments = 15,
  spawnInterval = 400,
  scale = 1,
}: DocumentRainProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const engineRef = useRef<Matter.Engine | null>(null);
  const runnerRef = useRef<Matter.Runner | null>(null);
  const rafRef = useRef<number | null>(null);
  const spawnTimerRef = useRef<number | null>(null);
  const documentCountRef = useRef(0);
  const isSpawningRef = useRef(true);
  const particlesRef = useRef<PoofParticle[]>([]);

  // Create poof particles at a position with a given color
  const createPoofParticles = useCallback((x: number, y: number, color: string) => {
    const particleCount = 12;
    const newParticles: PoofParticle[] = [];
    
    for (let i = 0; i < particleCount; i++) {
      const angle = (Math.PI * 2 * i) / particleCount + (Math.random() - 0.5) * 0.5;
      const speed = 3 + Math.random() * 4;
      
      newParticles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 2, // Slight upward bias
        size: 4 + Math.random() * 6,
        color,
        alpha: 1,
        decay: 0.02 + Math.random() * 0.02,
      });
    }
    
    // Add some smaller sparkle particles
    for (let i = 0; i < 8; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 5 + Math.random() * 3;
      
      newParticles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 1,
        size: 2 + Math.random() * 3,
        color: "#000000",
        alpha: 1,
        decay: 0.03 + Math.random() * 0.02,
      });
    }
    
    particlesRef.current.push(...newParticles);
  }, []);

  // Update and draw particles
  const updateAndDrawParticles = useCallback((ctx: CanvasRenderingContext2D) => {
    const particles = particlesRef.current;
    
    // Update particles
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.15; // Gravity
      p.alpha -= p.decay;
      p.size *= 0.97; // Shrink
      
      // Remove dead particles
      if (p.alpha <= 0 || p.size < 0.5) {
        particles.splice(i, 1);
      }
    }
    
    // Draw particles
    for (const p of particles) {
      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }, []);

  // Draw a single document shape on canvas
  const drawDocument = useCallback(
    (
      ctx: CanvasRenderingContext2D,
      x: number,
      y: number,
      angle: number,
      docScale: number,
      fillColor: string = "white"
    ) => {
      const w = DOC_WIDTH * docScale;
      const h = DOC_HEIGHT * docScale;

      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);

      // Scale factors from original 360x460 viewBox
      const sx = w / 360;
      const sy = h / 460;

      ctx.strokeStyle = "black";
      ctx.lineWidth = 2 * Math.min(sx, sy) * 10;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";

      // Main document outline
      ctx.beginPath();
      ctx.moveTo(-w / 2 + 10 * sx, -h / 2 + 10 * sy);
      ctx.lineTo(-w / 2 + 230 * sx, -h / 2 + 10 * sy);
      ctx.lineTo(-w / 2 + 350 * sx, -h / 2 + 130 * sy);
      ctx.lineTo(-w / 2 + 350 * sx, -h / 2 + 450 * sy);
      ctx.lineTo(-w / 2 + 10 * sx, -h / 2 + 450 * sy);
      ctx.closePath();
      ctx.fillStyle = fillColor;
      ctx.fill();
      ctx.stroke();

      // Folded corner
      ctx.beginPath();
      ctx.moveTo(-w / 2 + 340 * sx, -h / 2 + 130 * sy);
      ctx.lineTo(-w / 2 + 230 * sx, -h / 2 + 130 * sy);
      ctx.lineTo(-w / 2 + 230 * sx, -h / 2 + 20 * sy);
      ctx.stroke();

      // Text lines (filled rectangles)
      ctx.fillStyle = "black";
      ctx.fillRect(
        -w / 2 + 80 * sx,
        -h / 2 + 200 * sy,
        200 * sx,
        20 * sy
      );
      ctx.fillRect(
        -w / 2 + 80 * sx,
        -h / 2 + 260 * sy,
        160 * sx,
        20 * sy
      );
      ctx.fillRect(
        -w / 2 + 80 * sx,
        -h / 2 + 320 * sy,
        200 * sx,
        20 * sy
      );

      ctx.restore();
    },
    []
  );

  // Main effect: set up physics engine and render loop
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Get container dimensions
    const updateDimensions = () => {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
      return { width: rect.width, height: rect.height };
    };

    let { width, height } = updateDimensions();

    // Create Matter.js engine
    const engine = Matter.Engine.create({
      gravity: { x: 0, y: 0.5 },
    });
    engineRef.current = engine;

    const world = engine.world;

    // Document body dimensions
    const docW = DOC_WIDTH * scale;
    const docH = DOC_HEIGHT * scale;

    // Create boundaries (ground and walls)
    const wallThickness = 60;
    const ground = Matter.Bodies.rectangle(
      width / 2,
      height + wallThickness / 2 - 10,
      width * 2,
      wallThickness,
      { isStatic: true, label: "ground" }
    );
    const leftWall = Matter.Bodies.rectangle(
      -wallThickness / 2,
      height / 2,
      wallThickness,
      height * 2,
      { isStatic: true, label: "leftWall" }
    );
    const rightWall = Matter.Bodies.rectangle(
      width + wallThickness / 2,
      height / 2,
      wallThickness,
      height * 2,
      { isStatic: true, label: "rightWall" }
    );

    Matter.Composite.add(world, [ground, leftWall, rightWall]);

    // Spawn a document body
    const spawnDocument = () => {
      if (!isSpawningRef.current || documentCountRef.current >= maxDocuments) {
        isSpawningRef.current = false;
        if (spawnTimerRef.current) {
          clearInterval(spawnTimerRef.current);
          spawnTimerRef.current = null;
        }
        return;
      }

      // Random x position with margin
      const margin = docW;
      const x = margin + Math.random() * (width - 2 * margin);
      const y = -docH; // Start above viewport

      // Assign a random pastel color to this document
      const color = getRandomPastelColor();

      const doc = Matter.Bodies.rectangle(x, y, docW, docH, {
        label: "document",
        restitution: 0.2,
        friction: 0.8,
        frictionAir: 0.02,
        angle: (Math.random() - 0.5) * 0.5, // Slight random rotation
        plugin: { color }, // Store color in plugin data
      });

      Matter.Composite.add(world, doc);
      documentCountRef.current++;
    };

    // Start spawning documents
    spawnDocument(); // Spawn first immediately
    spawnTimerRef.current = window.setInterval(spawnDocument, spawnInterval);

    // Create runner for physics simulation
    const runner = Matter.Runner.create();
    runnerRef.current = runner;
    Matter.Runner.run(runner, engine);

    // Handle click to "poof" documents (listen on document to not block content)
    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Check if click is within canvas bounds
      if (mouseX < 0 || mouseX > rect.width || mouseY < 0 || mouseY > rect.height) {
        return;
      }

      // Query for bodies at click position
      const bodies = Matter.Composite.allBodies(world);
      
      for (const body of bodies) {
        if (body.label === "document") {
          // Check if click is within the document bounds
          if (Matter.Bounds.contains(body.bounds, { x: mouseX, y: mouseY })) {
            // Get the document's color for the poof effect
            const color = (body.plugin as { color?: string })?.color || "#FFE5E5";
            
            // Create poof particles at the document's position
            createPoofParticles(body.position.x, body.position.y, color);
            
            // Remove the document from the world
            Matter.Composite.remove(world, body);
            documentCountRef.current--;
            
            // Only poof one document per click
            break;
          }
        }
      }
    };

    // Listen on document so we don't block clicks to content above
    document.addEventListener("click", handleClick);

    // Render loop
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw all document bodies
      const bodies = Matter.Composite.allBodies(world);
      for (const body of bodies) {
        if (body.label === "document") {
          const color = (body.plugin as { color?: string })?.color || "white";
          drawDocument(ctx, body.position.x, body.position.y, body.angle, scale, color);
        }
      }

      // Draw poof particles
      updateAndDrawParticles(ctx);

      rafRef.current = requestAnimationFrame(render);
    };

    rafRef.current = requestAnimationFrame(render);

    // Handle resize
    const handleResize = () => {
      const dims = updateDimensions();
      width = dims.width;
      height = dims.height;

      // Update ground position
      Matter.Body.setPosition(ground, {
        x: width / 2,
        y: height + wallThickness / 2 - 10,
      });
      Matter.Body.setPosition(rightWall, {
        x: width + wallThickness / 2,
        y: height / 2,
      });
    };

    window.addEventListener("resize", handleResize);

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      document.removeEventListener("click", handleClick);

      if (spawnTimerRef.current) {
        clearInterval(spawnTimerRef.current);
      }
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      if (runnerRef.current) {
        Matter.Runner.stop(runnerRef.current);
      }
      if (engineRef.current) {
        Matter.Engine.clear(engineRef.current);
      }
      documentCountRef.current = 0;
      isSpawningRef.current = true;
      particlesRef.current = [];
    };
  }, [scale, maxDocuments, spawnInterval, drawDocument, createPoofParticles, updateAndDrawParticles]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 overflow-hidden pointer-events-none"
      style={{ zIndex: 0 }}
    >
      <canvas ref={canvasRef} className="w-full h-full" />
    </div>
  );
}
