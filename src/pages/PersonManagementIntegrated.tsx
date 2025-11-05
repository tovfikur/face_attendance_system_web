/**
 * Person Management - Integrated with Backend API
 * Full CRUD operations for person profiles with face enrollment
 */

import { useEffect, useState, useCallback } from 'react'
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Image as ImageIcon,
  Users,
  Loader2,
  RefreshCw,
  X,
  Check,
  AlertCircle,
} from 'lucide-react'
import { apiClient } from '@/services/apiClient'
import { useNotification } from '@/context/NotificationContext'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import type { FaceProfile } from '@/types'

interface PersonFormData {
  first_name: string
  last_name: string
  email: string
  phone?: string
  person_type: 'employee' | 'visitor' | 'contractor'
  id_number?: string
  id_type?: string
  department?: string
  organization?: string
  status: 'active' | 'inactive' | 'archived'
}

const initialFormData: PersonFormData = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  person_type: 'employee',
  id_number: '',
  id_type: '',
  department: '',
  organization: '',
  status: 'active',
}

export const PersonManagementIntegratedPage = () => {
  const { addNotification } = useNotification()

  // State management
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [persons, setPersons] = useState<FaceProfile[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    page: 1,
    pageSize: 20,
    status: 'all' as string,
    personType: 'all' as string,
    department: 'all' as string,
  })

  // Form state
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState<PersonFormData>(initialFormData)
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})

  // Fetch persons
  const fetchPersons = useCallback(async () => {
    try {
      setLoading(true)
      let response

      if (searchQuery) {
        response = await apiClient.searchPersons(searchQuery)
      } else {
        response = await apiClient.getPersons(filters.page, filters.pageSize, {
          status: filters.status === 'all' ? undefined : filters.status,
          personType: filters.personType === 'all' ? undefined : filters.personType,
          department: filters.department === 'all' ? undefined : filters.department,
        })
      }

      setPersons(response.data)
    } catch (err) {
      console.error('Failed to fetch persons:', err)
      addNotification('error', 'Failed to load persons')
    } finally {
      setLoading(false)
    }
  }, [searchQuery, filters, addNotification])

  // Validate form
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required'
    }
    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required'
    }
    if (!formData.email.trim()) {
      errors.email = 'Email is required'
    } else if (!formData.email.includes('@')) {
      errors.email = 'Invalid email format'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  // Create/Update person
  const handleSaveForm = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      addNotification('error', 'Please fix form errors')
      return
    }

    try {
      setSyncing(true)

      if (editingId) {
        // Update
        await apiClient.updatePerson(editingId, formData)
        addNotification('success', 'Person updated successfully')
      } else {
        // Create
        await apiClient.createPerson(formData)
        addNotification('success', 'Person created successfully')
      }

      setShowForm(false)
      setEditingId(null)
      setFormData(initialFormData)
      fetchPersons()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Operation failed'
      addNotification('error', 'Failed to save person', message)
    } finally {
      setSyncing(false)
    }
  }

  // Delete person
  const handleDelete = async (personId: string) => {
    if (!confirm('Are you sure you want to delete this person? This action cannot be undone.')) {
      return
    }

    try {
      setSyncing(true)
      await apiClient.deletePerson(personId)
      addNotification('success', 'Person deleted successfully')
      fetchPersons()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Delete failed'
      addNotification('error', 'Failed to delete person', message)
    } finally {
      setSyncing(false)
    }
  }

  // Edit person
  const handleEdit = (person: FaceProfile) => {
    setFormData({
      first_name: person.first_name,
      last_name: person.last_name,
      email: person.email || '',
      phone: person.phone || '',
      person_type: (person.person_type as any) || 'employee',
      id_number: person.id_number || '',
      id_type: person.id_type || '',
      department: person.department || '',
      organization: person.organization || '',
      status: (person.status as any) || 'active',
    })
    setEditingId(person.id)
    setShowForm(true)
  }

  // Close form
  const handleCloseForm = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData(initialFormData)
    setFormErrors({})
  }

  // Refresh data
  const handleRefresh = async () => {
    setSyncing(true)
    try {
      await fetchPersons()
      addNotification('success', 'Data refreshed', '', 2000)
    } catch (err) {
      addNotification('error', 'Refresh failed')
    } finally {
      setSyncing(false)
    }
  }

  // Initial fetch
  useEffect(() => {
    fetchPersons()
  }, [fetchPersons])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Person Management</h1>
          <p className="mt-2 text-slate-400">Manage employee and visitor profiles</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleRefresh}
            disabled={syncing}
            icon={syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            variant="outline"
          >
            Refresh
          </Button>
          <Button
            onClick={() => {
              setShowForm(true)
              setEditingId(null)
              setFormData(initialFormData)
            }}
            icon={<Plus className="h-4 w-4" />}
            variant="primary"
          >
            Add Person
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <Card className="border-slate-800/70">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <label className="block text-sm font-medium text-slate-300 mb-2">Search</label>
            <input
              type="text"
              placeholder="Search by name, email, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white placeholder-slate-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Type</label>
            <select
              value={filters.personType}
              onChange={(e) => setFilters((prev) => ({ ...prev, personType: e.target.value }))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
            >
              <option value="all">All Types</option>
              <option value="employee">Employee</option>
              <option value="visitor">Visitor</option>
              <option value="contractor">Contractor</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Department</label>
            <select
              value={filters.department}
              onChange={(e) => setFilters((prev) => ({ ...prev, department: e.target.value }))}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2 text-white"
            >
              <option value="all">All Departments</option>
              <option value="engineering">Engineering</option>
              <option value="sales">Sales</option>
              <option value="hr">HR</option>
              <option value="finance">Finance</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Persons Table */}
      <Card className="border-slate-800/70">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-white">Persons List</h2>
          <span className="text-sm text-slate-400">{persons.length} persons</span>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
          </div>
        ) : persons.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/50 p-8 text-center">
            <Users className="mx-auto h-12 w-12 text-slate-500 mb-4" />
            <p className="text-slate-400">No persons found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Type</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Department</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Faces</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {persons.map((person) => (
                  <tr key={person.id} className="border-b border-slate-800/50 hover:bg-slate-900/50">
                    <td className="px-4 py-3 text-white">
                      {person.first_name} {person.last_name}
                    </td>
                    <td className="px-4 py-3 text-slate-300 text-xs">{person.email}</td>
                    <td className="px-4 py-3">
                      <Badge
                        tone={
                          person.person_type === 'employee'
                            ? 'info'
                            : person.person_type === 'visitor'
                              ? 'warning'
                              : 'secondary'
                        }
                        soft
                      >
                        {person.person_type}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-300">{person.department || '-'}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <ImageIcon className="h-4 w-4 text-slate-400" />
                        <span className="text-white">{person.face_encoding_count || 0}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        tone={person.status === 'active' ? 'success' : 'danger'}
                        soft
                      >
                        {person.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        icon={<Edit2 className="h-3 w-3" />}
                        onClick={() => handleEdit(person)}
                        disabled={syncing}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        icon={<Trash2 className="h-3 w-3" />}
                        onClick={() => handleDelete(person.id)}
                        disabled={syncing}
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="max-w-md w-full border-slate-800/70">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-white">
                {editingId ? 'Edit Person' : 'Add New Person'}
              </h2>
              <button
                onClick={handleCloseForm}
                className="text-slate-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveForm} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">First Name *</label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, first_name: e.target.value }))
                    }
                    className={`w-full rounded-lg border ${
                      formErrors.first_name ? 'border-red-500' : 'border-slate-700'
                    } bg-slate-900 px-3 py-2 text-white focus:border-blue-500`}
                  />
                  {formErrors.first_name && (
                    <p className="mt-1 text-xs text-red-500">{formErrors.first_name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Last Name *</label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) =>
                      setFormData((prev) => ({ ...prev, last_name: e.target.value }))
                    }
                    className={`w-full rounded-lg border ${
                      formErrors.last_name ? 'border-red-500' : 'border-slate-700'
                    } bg-slate-900 px-3 py-2 text-white focus:border-blue-500`}
                  />
                  {formErrors.last_name && (
                    <p className="mt-1 text-xs text-red-500">{formErrors.last_name}</p>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Email *</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData((prev) => ({ ...prev, email: e.target.value }))}
                  className={`w-full rounded-lg border ${
                    formErrors.email ? 'border-red-500' : 'border-slate-700'
                  } bg-slate-900 px-3 py-2 text-white focus:border-blue-500`}
                />
                {formErrors.email && (
                  <p className="mt-1 text-xs text-red-500">{formErrors.email}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Type</label>
                <select
                  value={formData.person_type}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      person_type: e.target.value as any,
                    }))
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                >
                  <option value="employee">Employee</option>
                  <option value="visitor">Visitor</option>
                  <option value="contractor">Contractor</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Department</label>
                <input
                  type="text"
                  value={formData.department}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, department: e.target.value }))
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                  placeholder="e.g., Engineering"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, status: e.target.value as any }))
                  }
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-white"
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="archived">Archived</option>
                </select>
              </div>

              <div className="flex gap-2 pt-4">
                <Button
                  type="submit"
                  disabled={syncing}
                  icon={syncing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  variant="primary"
                  className="flex-1"
                >
                  {syncing ? 'Saving...' : 'Save'}
                </Button>
                <Button
                  type="button"
                  onClick={handleCloseForm}
                  disabled={syncing}
                  variant="outline"
                  className="flex-1"
                >
                  Cancel
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}
