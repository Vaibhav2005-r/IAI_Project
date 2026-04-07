import React from 'react';
import { useSpring, animated } from '@react-spring/three';
import { Chess, type Square } from 'chess.js';
import * as THREE from 'three';

// Glowing materials for absolute premium feel!
const whiteMaterial = new THREE.MeshPhysicalMaterial({
  color: '#ffffff',
  metalness: 0.2,
  roughness: 0.1,
  clearcoat: 1.0,
  transmission: 0.2,
  thickness: 0.5,
});

const blackMaterial = new THREE.MeshPhysicalMaterial({
  color: '#001a3a', // Deep Blue!
  metalness: 0.7,
  roughness: 0.2,
  clearcoat: 1.0,
  emissive: '#002255',
  emissiveIntensity: 0.2,
});



const PieceMesh = ({ type, material, isWhite }: { type: string, material: THREE.Material, isWhite: boolean }) => {
  switch (type) {
    case 'p':
      return (
        <group>
          <mesh material={material} castShadow receiveShadow position={[0, 0.1, 0]}><cylinderGeometry args={[0.35, 0.45, 0.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.5, 0]}><cylinderGeometry args={[0.2, 0.35, 0.7, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.9, 0]}><cylinderGeometry args={[0.25, 0.2, 0.05, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.15, 0]}><sphereGeometry args={[0.25, 32, 32]} /></mesh>
        </group>
      );
    case 'r':
      return (
        <group>
          <mesh material={material} castShadow receiveShadow position={[0, 0.1, 0]}><cylinderGeometry args={[0.45, 0.5, 0.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.6, 0]}><cylinderGeometry args={[0.35, 0.4, 0.8, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.1, 0]}><cylinderGeometry args={[0.45, 0.35, 0.3, 32]} /></mesh>
        </group>
      );
    case 'n':
      return (
        <group rotation={[0, isWhite ? Math.PI / 2 : -Math.PI / 2, 0]}>
          <mesh material={material} castShadow receiveShadow position={[0, 0.1, 0]}><cylinderGeometry args={[0.45, 0.5, 0.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.6, 0.1]} rotation={[-0.2, 0, 0]}><boxGeometry args={[0.4, 0.8, 0.6]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.05, 0.25]} rotation={[0.2, 0, 0]}><boxGeometry args={[0.35, 0.5, 0.6]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.25, -0.05]}><coneGeometry args={[0.15, 0.4, 4]} /></mesh>
        </group>
      );
    case 'b':
      return (
        <group>
          <mesh material={material} castShadow receiveShadow position={[0, 0.1, 0]}><cylinderGeometry args={[0.4, 0.45, 0.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.7, 0]}><cylinderGeometry args={[0.15, 0.35, 1.0, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.25, 0]}><cylinderGeometry args={[0.25, 0.15, 0.1, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.5, 0]}><sphereGeometry args={[0.2, 32, 16]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.75, 0]}><sphereGeometry args={[0.08, 16, 16]} /></mesh>
        </group>
      );
    case 'q':
      return (
        <group>
          <mesh material={material} castShadow receiveShadow position={[0, 0.1, 0]}><cylinderGeometry args={[0.45, 0.5, 0.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.8, 0]}><cylinderGeometry args={[0.2, 0.4, 1.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.45, 0]}><cylinderGeometry args={[0.4, 0.2, 0.1, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.7, 0]}><cylinderGeometry args={[0.45, 0.3, 0.4, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.95, 0]}><sphereGeometry args={[0.1, 16, 16]} /></mesh>
        </group>
      );
    case 'k':
      return (
        <group>
          <mesh material={material} castShadow receiveShadow position={[0, 0.1, 0]}><cylinderGeometry args={[0.45, 0.5, 0.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 0.8, 0]}><cylinderGeometry args={[0.25, 0.4, 1.2, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.45, 0]}><cylinderGeometry args={[0.4, 0.25, 0.1, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 1.7, 0]}><cylinderGeometry args={[0.3, 0.4, 0.4, 32]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 2.05, 0]}><boxGeometry args={[0.1, 0.4, 0.1]} /></mesh>
          <mesh material={material} castShadow receiveShadow position={[0, 2.05, 0]}><boxGeometry args={[0.3, 0.1, 0.1]} /></mesh>
        </group>
      );
    default:
      return null;
  }
};

const ChessPiece = ({ 
  type, 
  color, 
  position, 
  onClick 
}: { 
  type: string, 
  color: 'w' | 'b', 
  position: [number, number, number],
  onClick?: () => void
}) => {
  const { pos } = useSpring({
    pos: position,
    config: { mass: 1, tension: 170, friction: 26 },
  });

  const material = color === 'w' ? whiteMaterial : blackMaterial;

  return (
    <animated.group 
      position={pos as any} 
      onClick={(e: any) => {
        e.stopPropagation();
        if (onClick) onClick();
      }}
    >
      <PieceMesh type={type} material={material} isWhite={color === 'w'} />
    </animated.group>
  );
};

const BOARD_SIZE = 8;
const TILE_SIZE = 1.2;

export default function ChessBoard3D({ 
  game, 
  onMove 
}: { 
  game: Chess, 
  onMove: (source: Square, target: Square) => void 
}) {
  const [selectedSquare, setSelectedSquare] = React.useState<Square | null>(null);
  const [validMoves, setValidMoves] = React.useState<Square[]>([]);

  const board = game.board();

  const handleSquareClick = (square: Square) => {
    if (selectedSquare) {
      if (validMoves.includes(square)) {
        onMove(selectedSquare, square);
        setSelectedSquare(null);
        setValidMoves([]);
      } else {
        // change selection
        const piece = game.get(square);
        if (piece && piece.color === game.turn()) {
          setSelectedSquare(square);
          const moves = game.moves({ square, verbose: true });
          setValidMoves(moves.map(m => m.to as Square));
        } else {
          setSelectedSquare(null);
          setValidMoves([]);
        }
      }
    } else {
      const piece = game.get(square);
      if (piece && piece.color === game.turn()) {
        setSelectedSquare(square);
        const moves = game.moves({ square, verbose: true });
        setValidMoves(moves.map(m => m.to as Square));
      }
    }
  };

  const tiles = (() => {
    const list = [];
    const files = ['a','b','c','d','e','f','g','h'];
    for (let row = 0; row < BOARD_SIZE; row++) {
      for (let col = 0; col < BOARD_SIZE; col++) {
        const isBlack = (row + col) % 2 === 1;
        const square = `${files[col]}${8 - row}` as Square;
        const x = (col - BOARD_SIZE/2 + 0.5) * TILE_SIZE;
        const z = (row - BOARD_SIZE/2 + 0.5) * TILE_SIZE;
        
        list.push(
          <mesh 
            key={`${row}-${col}`} 
            position={[x, -0.1, z]} 
            receiveShadow
            onClick={(e) => {
              e.stopPropagation();
              handleSquareClick(square);
            }}
          >
            <boxGeometry args={[TILE_SIZE, 0.2, TILE_SIZE]} />
            <meshStandardMaterial 
              color={isBlack ? '#000a1a' : '#d8e5ff'} 
              roughness={0.1}
              metalness={0.6}
            />
          </mesh>
        );
      }
    }
    return list;
  })();

  const pieces = [];
  const files = ['a','b','c','d','e','f','g','h'];
  
  // Highlighting
  const highlights = [];

  for (let row = 0; row < BOARD_SIZE; row++) {
    for (let col = 0; col < BOARD_SIZE; col++) {
      const square = files[col] + (8 - row) as Square;
      const piece = board[row][col];
      const x = (col - BOARD_SIZE/2 + 0.5) * TILE_SIZE;
      const z = (row - BOARD_SIZE/2 + 0.5) * TILE_SIZE;
      
      if (piece) {
        const yOffset = 0.0;
        
        pieces.push(
          <ChessPiece 
            key={`${piece.color}-${piece.type}-${square}`} 
            type={piece.type} 
            color={piece.color} 
            position={[x, yOffset, z]}
            onClick={() => handleSquareClick(square)}
          />
        );
      }

      if (selectedSquare === square || validMoves.includes(square)) {
        highlights.push(
          <mesh key={`highlight-${square}`} position={[x, 0.05, z]} rotation={[-Math.PI/2, 0, 0]}>
            <planeGeometry args={[TILE_SIZE - 0.1, TILE_SIZE - 0.1]} />
            <meshBasicMaterial 
              color={selectedSquare === square ? '#ffaa00' : '#00ffff'} 
              transparent 
              opacity={0.6}
              depthWrite={false}
            />
          </mesh>
        );
      }
    }
  }

  return (
    <group>
      {/* Cool tech grid border */}
      <mesh position={[0, -0.25, 0]} receiveShadow>
        <boxGeometry args={[BOARD_SIZE * TILE_SIZE + 0.8, 0.3, BOARD_SIZE * TILE_SIZE + 0.8]} />
        <meshPhysicalMaterial color="#002255" metalness={0.9} roughness={0.1} clearcoat={1.0} />
      </mesh>
      
      {tiles}
      {highlights}
      {pieces}
    </group>
  );
}
