import React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"
import { ArrowUpDown, ChevronDown, MoreHorizontal, ExternalLink, Search } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

// Types
type Alumni = {
  id: number
  name: string
  graduation_year: number
  degree_program: string
  email?: string
  linkedin_url?: string
  imdb_url?: string
  website?: string
  created_at: string
  updated_at: string
}

// Degree program color mapping
const getDegreeColor = (program: string) => {
  const colors = {
    "Film Production": "bg-blue-100 text-blue-800 hover:bg-blue-200",
    "Documentary": "bg-green-100 text-green-800 hover:bg-green-200", 
    "Animation": "bg-purple-100 text-purple-800 hover:bg-purple-200",
    "Screenwriting": "bg-orange-100 text-orange-800 hover:bg-orange-200",
    "Television": "bg-pink-100 text-pink-800 hover:bg-pink-200",
  }
  return colors[program as keyof typeof colors] || "bg-gray-100 text-gray-800"
}

export const columns: ColumnDef<Alumni>[] = [
  {
    accessorKey: "name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-slate-100 -ml-4"
        >
          Name
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => (
      <div className="font-medium text-slate-900">{row.getValue("name")}</div>
    ),
  },
  {
    accessorKey: "graduation_year",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="hover:bg-slate-100 -ml-4"
        >
          Graduation Year
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => (
      <div className="text-slate-600">{row.getValue("graduation_year")}</div>
    ),
  },
  {
    accessorKey: "degree_program",
    header: "Degree Program",
    cell: ({ row }) => {
      const program = row.getValue("degree_program") as string
      return (
        <Badge className={getDegreeColor(program)} variant="secondary">
          {program}
        </Badge>
      )
    },
  },
  {
    accessorKey: "email",
    header: "Email",
    cell: ({ row }) => {
      const email = row.getValue("email") as string
      return (
        <div className="text-slate-600">
          {email ? (
            <a href={`mailto:${email}`} className="hover:text-blue-600 transition-colors">
              {email}
            </a>
          ) : (
            "N/A"
          )}
        </div>
      )
    },
  },
  {
    id: "links",
    header: "Links",
    cell: ({ row }) => {
      const alumni = row.original
      const links = [
        { url: alumni.linkedin_url, label: "LinkedIn", color: "text-blue-600" },
        { url: alumni.imdb_url, label: "IMDb", color: "text-yellow-600" },
        { url: alumni.website, label: "Website", color: "text-green-600" },
      ].filter(link => link.url)

      return (
        <div className="flex gap-2 flex-wrap">
          {links.length > 0 ? (
            links.map((link, index) => (
              <a
                key={index}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`${link.color} hover:underline text-sm flex items-center gap-1 transition-colors`}
              >
                {link.label}
                <ExternalLink className="h-3 w-3" />
              </a>
            ))
          ) : (
            <span className="text-slate-400 text-sm">No links</span>
          )}
        </div>
      )
    },
  },
]

export function AlumniDataTable() {
  const [data, setData] = React.useState<Alumni[]>([])
  const [loading, setLoading] = React.useState(true)
  const [sorting, setSorting] = React.useState<SortingState>([])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})

  // Fetch alumni data
  React.useEffect(() => {
    const fetchAlumni = async () => {
      try {
        const response = await fetch('/api/alumni')
        const alumni = await response.json()
        setData(alumni)
      } catch (error) {
        console.error('Error fetching alumni:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchAlumni()
  }, [])

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
    },
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  })

  if (loading) {
    return (
      <Card>
        <CardContent className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-slate-600">Loading alumni...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            👥 Alumni Directory
          </CardTitle>
          <CardDescription>
            Manage and view all alumni records with advanced filtering and sorting capabilities.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-4 flex-1">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search alumni..."
                  value={(table.getColumn("name")?.getFilterValue() as string) ?? ""}
                  onChange={(event) =>
                    table.getColumn("name")?.setFilterValue(event.target.value)
                  }
                  className="pl-10"
                />
              </div>
              
              <select
                className="px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={(table.getColumn("degree_program")?.getFilterValue() as string) ?? ""}
                onChange={(event) =>
                  table.getColumn("degree_program")?.setFilterValue(event.target.value || undefined)
                }
              >
                <option value="">All Degrees</option>
                <option value="Film Production">Film Production</option>
                <option value="Documentary">Documentary</option>
                <option value="Animation">Animation</option>
                <option value="Screenwriting">Screenwriting</option>
                <option value="Television">Television</option>
              </select>
            </div>
            
            <div className="text-sm text-slate-600">
              {table.getFilteredRowModel().rows.length} of {data.length} alumni
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-hidden">
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id} className="hover:bg-transparent border-b border-slate-200">
                    {headerGroup.headers.map((header) => {
                      return (
                        <TableHead key={header.id} className="bg-slate-50">
                          {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                        </TableHead>
                      )
                    })}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows?.length ? (
                  table.getRowModel().rows.map((row) => (
                    <TableRow
                      key={row.id}
                      data-state={row.getIsSelected() && "selected"}
                      className="hover:bg-slate-50 transition-colors"
                    >
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(
                            cell.column.columnDef.cell,
                            cell.getContext()
                          )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center text-slate-500"
                    >
                      No alumni found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50">
          <div className="text-sm text-slate-600">
            Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{" "}
            {Math.min(
              (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
              table.getFilteredRowModel().rows.length
            )}{" "}
            of {table.getFilteredRowModel().rows.length} entries
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="border-slate-300"
            >
              Previous
            </Button>
            <span className="text-sm text-slate-600 px-3">
              Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="border-slate-300"
            >
              Next
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
