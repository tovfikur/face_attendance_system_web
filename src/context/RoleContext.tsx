import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { roles as mockRoles } from '@/data/mockData'
import type { Role } from '@/types'

interface RoleContextValue {
  roles: Role[]
  activeRole: Role
  setActiveRole: (roleId: Role['id']) => void
}

const RoleContext = createContext<RoleContextValue | undefined>(undefined)

export const RoleProvider = ({ children }: { children: ReactNode }) => {
  const [roleId, setRoleId] = useState<Role['id']>(mockRoles[0].id)

  const value = useMemo<RoleContextValue>(() => {
    const activeRole = mockRoles.find((role) => role.id === roleId) ?? mockRoles[0]
    return {
      roles: mockRoles,
      activeRole,
      setActiveRole: setRoleId,
    }
  }, [roleId])

  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>
}

export const useRoleContext = () => {
  const ctx = useContext(RoleContext)
  if (!ctx) {
    throw new Error('useRoleContext must be used within RoleProvider')
  }
  return ctx
}
