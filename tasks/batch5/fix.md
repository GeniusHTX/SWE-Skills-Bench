# Task: Fix React Component Bugs and Add ESLint Auto-Fix Configuration

## Background

Upgradle (https://github.com/michaelasper/upgradle) is a small React-based web application. The codebase has several issues: broken component rendering due to incorrect state management, missing prop validation, and inconsistent code style. This task requires fixing the bugs, adding proper TypeScript types, configuring ESLint with auto-fixable rules, and verifying the fixes through tests.

## Files to Create/Modify

- `src/components/GameBoard.tsx` (modify) — Fix state mutation bug: the component directly mutates an array state variable instead of creating a new array. Replace `state.push(item)` patterns with immutable updates using spread operator or `concat`. Fix the `useEffect` dependency array warnings.
- `src/components/ScoreDisplay.tsx` (modify) — Fix conditional rendering issue: the component renders `0` as falsy (blank) instead of displaying the score "0". Replace `{score && <span>{score}</span>}` with proper null check `{score != null && <span>{score}</span>}`.
- `src/components/Timer.tsx` (modify) — Fix memory leak: `setInterval` is not cleaned up on unmount. Add return cleanup function to `useEffect`. Fix the interval drift by using `useRef` for tracking elapsed time.
- `src/types/game.ts` (create) — TypeScript interfaces: `GameState`, `Player`, `Round`, `ScoreEntry` with proper types for all component props.
- `.eslintrc.json` (create) — ESLint configuration: extend `react-app`, add rules for `react-hooks/exhaustive-deps` (error), `no-direct-mutation-of-state` (error), `prefer-const` (warn), `@typescript-eslint/no-unused-vars` (error).
- `src/__tests__/GameBoard.test.tsx` (create) — Tests verifying: state updates create new array references, score of 0 displays correctly, timer cleans up on unmount.

## Requirements

### GameBoard State Mutation Fix

- Identify every instance where state is mutated directly (e.g., `items.push()`, `items[i] = value`, `items.splice()`) and replace with immutable patterns.
- After fix: `setItems(prev => [...prev, newItem])` instead of `items.push(newItem); setItems(items)`.
- Ensure each state update triggers a re-render by creating a new reference.

### ScoreDisplay Rendering Fix

- The current code `{score && <Display />}` renders nothing when `score === 0` because `0` is falsy in JavaScript.
- Fix: use explicit null/undefined check: `{score !== null && score !== undefined && <Display value={score} />}`.
- Also handle the edge case where score is `NaN` — display "—" instead.

### Timer Memory Leak Fix

- The current `useEffect` calls `setInterval` but has no cleanup return.
- Add: `return () => clearInterval(intervalRef.current)` to the effect.
- Fix interval drift: store `startTime` in a ref, compute elapsed as `Date.now() - startTime` instead of incrementing a counter.
- Handle component re-mount: reset the timer when the `isActive` prop changes.

### TypeScript Interfaces

```typescript
interface GameState {
  rounds: Round[];
  currentRound: number;
  players: Player[];
  isActive: boolean;
  startedAt: Date | null;
}

interface Player {
  id: string;
  name: string;
  scores: ScoreEntry[];
}

interface Round {
  number: number;
  word: string;
  timeLimit: number;
  completedAt: Date | null;
}

interface ScoreEntry {
  roundNumber: number;
  value: number;
  bonus: number;
}
```

### ESLint Configuration

- Parser: `@typescript-eslint/parser`.
- Plugins: `@typescript-eslint`, `react`, `react-hooks`.
- Rules: `react-hooks/rules-of-hooks: error`, `react-hooks/exhaustive-deps: error`, `no-array-mutation: off` (use TypeScript readonly instead), `prefer-const: warn`.
- Environment: `browser`, `es2021`, `jest`.

### Expected Functionality

- After fix: adding an item to the game board triggers a re-render showing the new item.
- Score of 0 displays as "0" (not blank).
- Unmounting the Timer component clears the interval (no console warnings about state updates on unmounted components).
- `npx eslint src/ --fix` runs without errors on the fixed code.

## Acceptance Criteria

- No direct state mutations exist in any component (all state updates use setter functions with new references).
- Score value of `0` renders correctly in the UI.
- Timer `useEffect` includes a cleanup function that clears the interval.
- TypeScript interfaces are defined and imported by the components.
- ESLint configuration is present and all source files pass linting.
- Tests verify each bug fix: immutable state update, zero-score display, and timer cleanup.
