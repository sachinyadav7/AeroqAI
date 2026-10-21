import React, { useRef, useEffect } from 'react';

/**
 * Interactive 3D Neural Geodesic Sphere
 * Inspired by image_3.jpg: A subtle rotating particle sphere representing the AI Evaluation Engine.
 * Self-contained HTML5 Canvas implementation (60 FPS, zero dependencies, theme-adaptive).
 */
export default function NeuralSphere({ size = 260, theme = 'dark' }) {
  const canvasRef = useRef(null);
  const rotationRef = useRef({ x: 0.3, y: 0.2 });
  const isDraggingRef = useRef(false);
  const lastMousePosRef = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    // Generate geodesic icosahedron vertices on a sphere
    const vertices = [];
    const phi = (1 + Math.sqrt(5)) / 2; // Golden ratio
    const radius = size * 0.38;

    // Base icosahedron points
    const basePoints = [
      [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
      [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
      [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
    ];

    // Normalize to sphere radius
    basePoints.forEach(([x, y, z]) => {
      const len = Math.sqrt(x * x + y * y + z * z);
      vertices.push({
        x: (x / len) * radius,
        y: (y / len) * radius,
        z: (z / len) * radius,
        pulseOffset: Math.random() * Math.PI * 2
      });
    });

    // Subdivide to create more geodesic density (midpoints)
    const count = vertices.length;
    for (let i = 0; i < count; i++) {
      for (let j = i + 1; j < count; j++) {
        const dx = vertices[i].x - vertices[j].x;
        const dy = vertices[i].y - vertices[j].y;
        const dz = vertices[i].z - vertices[j].z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
        if (dist < radius * 1.15) {
          const mx = (vertices[i].x + vertices[j].x) / 2;
          const my = (vertices[i].y + vertices[j].y) / 2;
          const mz = (vertices[i].z + vertices[j].z) / 2;
          const mlen = Math.sqrt(mx * mx + my * my + mz * mz);
          vertices.push({
            x: (mx / mlen) * radius,
            y: (my / mlen) * radius,
            z: (mz / mlen) * radius,
            pulseOffset: Math.random() * Math.PI * 2
          });
        }
      }
    }

    let time = 0;

    const render = () => {
      time += 0.015;
      ctx.clearRect(0, 0, size, size);

      // Auto rotation when not dragging
      if (!isDraggingRef.current) {
        rotationRef.current.x += 0.003;
        rotationRef.current.y += 0.005;
      }

      const rotX = rotationRef.current.x;
      const rotY = rotationRef.current.y;
      const cosX = Math.cos(rotX), sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY), sinY = Math.sin(rotY);

      // Project vertices to 2D
      const projected = vertices.map((v) => {
        // Rotate around Y
        let x1 = v.x * cosY + v.z * sinY;
        let z1 = -v.x * sinY + v.z * cosY;
        // Rotate around X
        let y2 = v.y * cosX - z1 * sinX;
        let z2 = v.y * sinX + z1 * cosX;

        // Perspective projection
        const fov = 400;
        const scale = fov / (fov + z2);
        const px = size / 2 + x1 * scale;
        const py = size / 2 + y2 * scale;

        return { px, py, z: z2, scale, pulseOffset: v.pulseOffset };
      });

      // Colors based on active theme
      const isDark = theme === 'dark';
      const edgeColorCyan = isDark ? 'rgba(32, 197, 231, ' : 'rgba(8, 157, 187, ';
      const edgeColorViolet = isDark ? 'rgba(117, 103, 255, ' : 'rgba(99, 91, 238, ';

      // Draw connecting edges
      const edgeDistThreshold = radius * 0.72;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const p1 = projected[i];
          const p2 = projected[j];
          const dx = p1.px - p2.px;
          const dy = p1.py - p2.py;
          const dist2D = Math.sqrt(dx * dx + dy * dy);

          if (dist2D < edgeDistThreshold) {
            const avgZ = (p1.z + p2.z) / 2;
            const alpha = Math.max(0.04, Math.min(0.55, (avgZ + radius) / (2 * radius)));
            const gradient = ctx.createLinearGradient(p1.px, p1.py, p2.px, p2.py);
            gradient.addColorStop(0, `${edgeColorCyan}${alpha})`);
            gradient.addColorStop(1, `${edgeColorViolet}${alpha * 0.8})`);

            ctx.beginPath();
            ctx.moveTo(p1.px, p1.py);
            ctx.lineTo(p2.px, p2.py);
            ctx.strokeStyle = gradient;
            ctx.lineWidth = 1 * ((p1.scale + p2.scale) / 2);
            ctx.stroke();
          }
        }
      }

      // Draw node points
      projected.forEach((p) => {
        const pulse = Math.sin(time * 2 + p.pulseOffset) * 0.5 + 0.5;
        const depthAlpha = Math.max(0.15, Math.min(1, (p.z + radius) / (2 * radius)));
        const r = (2 + pulse * 1.5) * p.scale;

        // Outer glow
        const glowRad = r * 3;
        const radialGrad = ctx.createRadialGradient(p.px, p.py, 0, p.px, p.py, glowRad);
        radialGrad.addColorStop(0, isDark ? `rgba(32, 197, 231, ${depthAlpha * 0.8})` : `rgba(99, 91, 238, ${depthAlpha * 0.6})`);
        radialGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

        ctx.beginPath();
        ctx.arc(p.px, p.py, glowRad, 0, Math.PI * 2);
        ctx.fillStyle = radialGrad;
        ctx.fill();

        // Core point
        ctx.beginPath();
        ctx.arc(p.px, p.py, r, 0, Math.PI * 2);
        ctx.fillStyle = isDark ? '#FFFFFF' : '#635BEE';
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [size, theme]);

  // Mouse drag interaction
  const handleMouseDown = (e) => {
    isDraggingRef.current = true;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMousePosRef.current.x;
    const dy = e.clientY - lastMousePosRef.current.y;
    rotationRef.current.y += dx * 0.008;
    rotationRef.current.x += dy * 0.008;
    lastMousePosRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  return (
    <div 
      style={{ 
        width: size, 
        height: size, 
        position: 'relative',
        cursor: 'grab',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      title="Interactive AI Neural Geodesic Sphere • Click & Drag to Rotate"
    >
      <canvas 
        ref={canvasRef} 
        style={{ width: size, height: size, display: 'block' }} 
      />
    </div>
  );
}
