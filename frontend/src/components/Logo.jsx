import { Group, Text } from '@mantine/core';

export default function Logo({ size = 28 }) {
  return (
    <Group gap={8} align="center" style={{ userSelect: 'none' }}>
      {/* Film-reel SVG */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        aria-label="CinemaList logo"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="16" cy="16" r="13" stroke="#e2b04a" strokeWidth="2" />
        <circle cx="16" cy="16" r="4" fill="#e2b04a" />
        {/* Spokes */}
        {[0, 60, 120, 180, 240, 300].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const x1 = 16 + 6 * Math.cos(rad);
          const y1 = 16 + 6 * Math.sin(rad);
          const x2 = 16 + 11 * Math.cos(rad);
          const y2 = 16 + 11 * Math.sin(rad);
          return (
            <line
              key={angle}
              x1={x1.toFixed(2)} y1={y1.toFixed(2)}
              x2={x2.toFixed(2)} y2={y2.toFixed(2)}
              stroke="#e2b04a"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          );
        })}
        {/* Sprocket holes */}
        {[30, 90, 150, 210, 270, 330].map((angle) => {
          const rad = (angle * Math.PI) / 180;
          const cx = 16 + 10 * Math.cos(rad);
          const cy = 16 + 10 * Math.sin(rad);
          return <circle key={angle} cx={cx.toFixed(2)} cy={cy.toFixed(2)} r="1.5" fill="#e2b04a" />;
        })}
      </svg>
      <Text fw={700} size="lg" style={{ color: '#e2b04a', letterSpacing: '-0.02em' }}>
        Cinema<Text span style={{ color: '#C9C9C9', fontWeight: 400 }}>List</Text>
      </Text>
    </Group>
  );
}
