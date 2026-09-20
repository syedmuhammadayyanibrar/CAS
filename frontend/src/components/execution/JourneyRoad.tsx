import React from "react";
import { JourneyCar } from "./JourneyCar";
import { MilestoneItem } from "./JourneyDestination";

interface JourneyRoadProps {
  milestones: MilestoneItem[];
  currentIndex: number;
  isRunning?: boolean;
  isPaused?: boolean;
}

export function JourneyRoad({
  milestones,
  currentIndex,
  isRunning = false,
  isPaused = false,
}: JourneyRoadProps) {
  const total = milestones.length;
  // Canvas width 1000, height 74
  const startX = 60;
  const endX = 940;
  const stepX = (endX - startX) / Math.max(1, total - 1);

  // Compute position for current index
  const safeIndex = Math.max(0, Math.min(currentIndex, total - 1));
  const carTargetX = startX + safeIndex * stepX - 28;
  const carTargetY = 14;

  return (
    <div className="w-full overflow-x-auto py-2">
      <svg
        viewBox="0 0 1000 74"
        className="w-full min-w-[760px] h-auto select-none"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="roadGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#E2E8F0" />
            <stop offset="100%" stopColor="#CBD5E1" />
          </linearGradient>
          <filter id="roadGlow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="1" stdDeviation="1" floodColor="#0F172A" floodOpacity="0.08" />
          </filter>
        </defs>

        {/* Outer Grass / Verge shoulder */}
        <rect x="20" y="24" width="960" height="42" rx="6" fill="#F1F5F9" />

        {/* Road Surface */}
        <rect
          x="30"
          y="28"
          width="940"
          height="34"
          rx="4"
          fill="url(#roadGradient)"
          stroke="#94A3B8"
          strokeWidth="1"
          filter="url(#roadGlow)"
        />

        {/* Road Shoulders / Curbs */}
        <line x1="30" y1="28" x2="970" y2="28" stroke="#E2E8F0" strokeWidth="2" />
        <line x1="30" y1="62" x2="970" y2="62" stroke="#64748B" strokeWidth="1" />

        {/* Center Dash Line */}
        <line
          x1="45"
          y1="45"
          x2="955"
          y2="45"
          stroke="#FFFFFF"
          strokeWidth="2.5"
          strokeDasharray="14 12"
          strokeLinecap="round"
        />

        {/* Milestone Station Marks on Road */}
        {milestones.map((m, idx) => {
          const mx = startX + idx * stepX;
          const isPassed = idx < safeIndex || m.status === "COMPLETED";
          const isCurrent = idx === safeIndex;

          return (
            <g key={m.id} transform={`translate(${mx}, 45)`}>
              {/* Station Stop Ring */}
              <circle
                cx="0"
                cy="0"
                r={isCurrent ? 7 : 5}
                fill={
                  isCurrent
                    ? "#2563EB"
                    : isPassed
                    ? "#059669"
                    : m.status === "PAUSED_FOR_HUMAN"
                    ? "#D97706"
                    : "#CBD5E1"
                }
                stroke="#FFFFFF"
                strokeWidth={isCurrent ? 2.5 : 1.5}
              />
              {isCurrent && (
                <circle
                  cx="0"
                  cy="0"
                  r="12"
                  fill="none"
                  stroke="#3B82F6"
                  strokeWidth="1.5"
                  opacity="0.4"
                  className="animate-ping"
                />
              )}
            </g>
          );
        })}

        {/* Animated Vector Car Traveling Along Road */}
        <JourneyCar
          x={carTargetX}
          y={carTargetY}
          isRunning={isRunning}
          isPaused={isPaused}
        />
      </svg>
    </div>
  );
}
