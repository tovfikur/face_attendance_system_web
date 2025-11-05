import { clsx } from 'clsx'
import type { Camera, CameraSummary } from '@/types'
import { CameraStreamTile } from '@/components/camera/CameraStreamTile'

type GridMode = '2x2' | '3x3'

interface CameraStreamGridProps {
  cameras: Camera[]
  summaries?: Map<string, CameraSummary>
  mode: GridMode
  activeCameraId?: string
  onSelect?: (cameraId: string) => void
}

const gridColumns: Record<GridMode, string> = {
  '2x2': 'sm:grid-cols-2 xl:grid-cols-2 2xl:grid-cols-3',
  '3x3': 'sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4',
}

export const CameraStreamGrid = ({
  cameras,
  summaries,
  mode,
  activeCameraId,
  onSelect,
}: CameraStreamGridProps) => {
  if (!cameras.length) {
    return (
      <div className="flex min-h-[200px] items-center justify-center rounded-xl border border-dashed border-slate-700/70 bg-slate-900/50 text-sm text-slate-400">
        Waiting for camera telemetry feed...
      </div>
    )
  }

  return (
    <div
      className={clsx(
        'grid gap-4 transition-[grid-template-columns] duration-300',
        gridColumns[mode],
      )}
    >
      {cameras.map((camera) => (
        <CameraStreamTile
          key={camera.id}
          camera={camera}
          summary={summaries?.get(camera.id)}
          active={camera.id === activeCameraId}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}
