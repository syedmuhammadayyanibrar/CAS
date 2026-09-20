import React from "react";

interface JourneyCarProps {
  x: number;
  y: number;
  isPaused?: boolean;
  isRunning?: boolean;
  className?: string;
}

/**
 * Clean, flat vector SVG car with restrained blue body (#2563EB),
 * subtle styling, flat wheels, and soft lighting.
 * No 3D, no emoji, strictly enterprise vector illustration.
 */
export function JourneyCar({ x, y, isPaused = false, isRunning = false, className = "" }: JourneyCarProps) {
  return (
    <g
      className={`transition-transform duration-900 ease-in-out ${className}`}
      style={{
        transform: `translate(${x}px, ${y}px)`,
        willChange: "transform",
      }}
    >
      {/* Drop Shadow under the car */}
      <ellipse cx="28" cy="23" rx="24" ry="3" fill="#94A3B8" opacity="0.35" />

      {/* Main Chassis / Car Body */}
      <path
        d="M 6 15 
           L 14 8 
           L 36 8 
           L 46 13 
           L 52 14 
           Q 54 15 54 18 
           L 54 20 
           L 2 20 
           Q 2 17 4 16 
           Z"
        fill="#2563EB"
        stroke="#1D4ED8"
        strokeWidth="1"
        strokeLinejoin="round"
      />

      {/* Cabin Roof Trim */}
      <path
        d="M 15 8.5 L 35 8.5 L 43 13 L 13 13 Z"
        fill="#1E40AF"
      />

      {/* Front Windshield */}
      <polygon points="35.5,9 42,13 35.5,13" fill="#E0F2FE" opacity="0.9" />

      {/* Side Cabin Windows */}
      <rect x="23" y="9" width="11" height="4" rx="0.5" fill="#E0F2FE" opacity="0.9" />
      <polygon points="15,13 17,9 21.5,9 21.5,13" fill="#E0F2FE" opacity="0.9" />

      {/* Front Headlight */}
      <path
        d="M 52 15 L 54 15 Q 54 17 53 18 L 51 18 Z"
        fill="#FDE047"
      />
      {/* Headlight beam glow when running */}
      {isRunning && (
        <polygon
          points="54,15 72,13 72,21 54,18"
          fill="#FEF08A"
          opacity="0.25"
        />
      )}

      {/* Rear Taillight */}
      <rect x="2" y="16" width="2" height="3" rx="0.5" fill="#EF4444" />

      {/* Door Line */}
      <line x1="22" y1="13" x2="22" y2="19" stroke="#1D4ED8" strokeWidth="0.8" />
      <rect x="24" y="15" width="3" height="1" rx="0.5" fill="#1E3A8A" />

      {/* Rear Wheel */}
      <g transform="translate(12, 20)">
        <circle cx="0" cy="0" r="5" fill="#334155" stroke="#1E293B" strokeWidth="1" />
        <circle cx="0" cy="0" r="2.5" fill="#CBD5E1" />
        <circle cx="0" cy="0" r="1" fill="#0F172A" />
      </g>

      {/* Front Wheel */}
      <g transform="translate(42, 20)">
        <circle cx="0" cy="0" r="5" fill="#334155" stroke="#1E293B" strokeWidth="1" />
        <circle cx="0" cy="0" r="2.5" fill="#CBD5E1" />
        <circle cx="0" cy="0" r="1" fill="#0F172A" />
      </g>

      {/* Paused alert marker if HITL */}
      {isPaused && (
        <g transform="translate(24, -8)">
          <circle cx="4" cy="4" r="7" fill="#FEF3C7" stroke="#F59E0B" strokeWidth="1.5" />
          <text
            x="4"
            y="7.5"
            textAnchor="middle"
            fontSize="9"
            fontWeight="bold"
            fill="#B45309"
          >
            !
          </text>
        </g>
      )}
    </g>
  );
}
