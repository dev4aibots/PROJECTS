// Per-icon imports keep the bundle and build memory small. The package barrel
// (`@phosphor-icons/react`) pulls 1,500+ icons x 6 weights into the module graph and
// exhausted a 1 GB build container. Add icons here, never import the barrel directly.
// The /dist/ssr entries render identically on the server and in client components.
export { ArrowCounterClockwise } from '@phosphor-icons/react/dist/ssr/ArrowCounterClockwise';
export { ArrowLeft } from '@phosphor-icons/react/dist/ssr/ArrowLeft';
export { ArrowRight } from '@phosphor-icons/react/dist/ssr/ArrowRight';
export { ArrowUpRight } from '@phosphor-icons/react/dist/ssr/ArrowUpRight';
export { BookOpen } from '@phosphor-icons/react/dist/ssr/BookOpen';
export { CalendarBlank } from '@phosphor-icons/react/dist/ssr/CalendarBlank';
export { Check } from '@phosphor-icons/react/dist/ssr/Check';
export { CheckCircle } from '@phosphor-icons/react/dist/ssr/CheckCircle';
export { CirclesFour } from '@phosphor-icons/react/dist/ssr/CirclesFour';
export { Columns } from '@phosphor-icons/react/dist/ssr/Columns';
export { Database } from '@phosphor-icons/react/dist/ssr/Database';
export { Flask } from '@phosphor-icons/react/dist/ssr/Flask';
export { FolderSimple } from '@phosphor-icons/react/dist/ssr/FolderSimple';
export { Info } from '@phosphor-icons/react/dist/ssr/Info';
export { ListBullets } from '@phosphor-icons/react/dist/ssr/ListBullets';
export { MagnifyingGlass } from '@phosphor-icons/react/dist/ssr/MagnifyingGlass';
export { Plus } from '@phosphor-icons/react/dist/ssr/Plus';
export { SquaresFour } from '@phosphor-icons/react/dist/ssr/SquaresFour';
export { WarningCircle } from '@phosphor-icons/react/dist/ssr/WarningCircle';
export { X } from '@phosphor-icons/react/dist/ssr/X';
export type { IconProps } from '@phosphor-icons/react/dist/lib/types';
