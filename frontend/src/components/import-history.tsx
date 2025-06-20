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
import { ArrowUpDown, Calendar, FileText, AlertCircle, CheckCircle, Clock, ChevronDown, ChevronRight } from "lucide-react"

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
type ImportHistory = {
  id: number
  filename: string
  import_type: string
  status: string
  total_records: number | null
  successful_records: number | null
  failed_records: number | null
  imported_by: string
  created_at: string
  completed_at: string | null
}

// Status color mapping
const getStatusColor = (status: string) => {
  const colors = {
    "completed": "bg-green-100 text-green-800 hover:bg-green-200",
    "partial": "bg-amber-100 text-amber-800 hover:bg-amber-200",
    "failed": "bg-red-100 text-red-800 hover:bg-red-200",
    "processing": "bg-blue-100 text-blue-800 hover:bg-blue-200",
  }
  return colors[status as keyof typeof colors] || "bg-gray-100 text-gray-800"
}

// Status icon mapping
const getStatusIcon = (status: string) => {
  switch (status) {
    case "completed":
      return <CheckCircle className="h-4 w-4" />
    case "partial":
      return <AlertCircle className="h-4 w-4" />
    case "failed":
      return <AlertCircle className="h-4 w-4" />
    case "processing":
      return <Clock className="h-4 w-4" />
    default:
      return <FileText className="h-4 w-4" />
  }
}

// Format date
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

// Calculate success rate
const getSuccessRate = (successful: number | null, total: number | null) => {
  if (!successful || !total || total === 0) return "N/A"
  return `${Math.round((successful / total) * 100)}%`
}

export function ImportHistory() {
  const [data, setData] = React.useState<ImportHistory[]>([])
  const [loading, setLoading] = React.useState(true)
  const [sorting, setSorting] = React.useState<SortingState>([{ id: "created_at", desc: true }])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState({})
  const [expandedRows, setExpandedRows] = React.useState<Set<number>>(new Set())

  // Fetch import history data
  React.useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('/api/import-history')
        const history = await response.json()
        setData(history)
      } catch (error) {
        console.error('Error fetching import history:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [])

  const columns: ColumnDef<ImportHistory>[] = [
    {
      id: "expand",
      header: "",
      cell: ({ row }) => {
        const isExpanded = expandedRows.has(row.original.id)
        const hasDetails = row.original.failed_records && row.original.failed_records > 0
        
        if (!hasDetails) return null
        
        return (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              const newExpanded = new Set(expandedRows)
              if (isExpanded) {
                newExpanded.delete(row.original.id)
              } else {
                newExpanded.add(row.original.id)
              }
              setExpandedRows(newExpanded)
            }}
            className="p-0 h-6 w-6"
          >
            {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        )
      },
      size: 40,
    },
    {
      accessorKey: "filename",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="hover:bg-slate-100 -ml-4"
          >
            Filename
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => (
        <div className="flex items-center space-x-2">
          <FileText className="h-4 w-4 text-slate-500" />
          <span className="font-medium text-slate-900">{row.getValue("filename")}</span>
        </div>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const status = row.getValue("status") as string
        return (
          <Badge className={getStatusColor(status)} variant="secondary">
            <div className="flex items-center space-x-1">
              {getStatusIcon(status)}
              <span className="capitalize">{status}</span>
            </div>
          </Badge>
        )
      },
    },
    {
      accessorKey: "total_records",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="hover:bg-slate-100 -ml-4"
          >
            Records
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => {
        const total = row.getValue("total_records") as number | null
        const successful = row.original.successful_records
        const failed = row.original.failed_records
        
        if (!total) return <span className="text-slate-400">N/A</span>
        
        return (
          <div className="text-sm">
            <div className="font-medium text-slate-900">{total} total</div>
            <div className="text-slate-600">
              {successful && <span className="text-green-600">{successful} ✓</span>}
              {successful && failed && " • "}
              {failed && failed > 0 && <span className="text-red-600">{failed} ✗</span>}
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: "success_rate",
      header: "Success Rate",
      cell: ({ row }) => {
        const successful = row.original.successful_records
        const total = row.getValue("total_records") as number | null
        const rate = getSuccessRate(successful, total)
        
        return (
          <div className="text-sm">
            {rate !== "N/A" ? (
              <div className={`font-medium ${
                rate === "100%" ? "text-green-600" : 
                parseInt(rate) >= 80 ? "text-amber-600" : 
                "text-red-600"
              }`}>
                {rate}
              </div>
            ) : (
              <span className="text-slate-400">N/A</span>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: "created_at",
      header: ({ column }) => {
        return (
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="hover:bg-slate-100 -ml-4"
          >
            Import Date
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        )
      },
      cell: ({ row }) => {
        const date = row.getValue("created_at") as string
        return (
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-slate-500" />
            <div className="text-sm">
              <div className="text-slate-900">{formatDate(date)}</div>
            </div>
          </div>
        )
      },
    },
    {
      accessorKey: "imported_by",
      header: "Imported By",
      cell: ({ row }) => (
        <div className="text-sm text-slate-600 capitalize">
          {row.getValue("imported_by")}
        </div>
      ),
    },
  ]

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
            <span className="ml-2 text-slate-600">Loading import history...</span>
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
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-6 w-6 text-blue-600" />
            <span>Import History</span>
          </CardTitle>
          <CardDescription>
            Track all CSV import activities with detailed status information, success rates, and error details.
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Stats Cards */}
      {data.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <div>
                  <p className="text-sm text-slate-600">Total Imports</p>
                  <p className="text-2xl font-bold text-slate-900">{data.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div>
                  <p className="text-sm text-slate-600">Successful</p>
                  <p className="text-2xl font-bold text-green-600">
                    {data.filter(item => item.status === 'completed').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                <div>
                  <p className="text-sm text-slate-600">Partial</p>
                  <p className="text-2xl font-bold text-amber-600">
                    {data.filter(item => item.status === 'partial').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <div>
                  <p className="text-sm text-slate-600">Failed</p>
                  <p className="text-2xl font-bold text-red-600">
                    {data.filter(item => item.status === 'failed').length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between space-x-4">
            <div className="flex items-center space-x-4 flex-1">
              <div className="relative flex-1 max-w-sm">
                <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by filename..."
                  value={(table.getColumn("filename")?.getFilterValue() as string) ?? ""}
                  onChange={(event) =>
                    table.getColumn("filename")?.setFilterValue(event.target.value)
                  }
                  className="pl-10"
                />
              </div>
              
              <select
                className="px-3 py-2 border border-input bg-background rounded-md text-sm"
                value={(table.getColumn("status")?.getFilterValue() as string) ?? ""}
                onChange={(event) =>
                  table.getColumn("status")?.setFilterValue(event.target.value || undefined)
                }
              >
                <option value="">All Status</option>
                <option value="completed">Completed</option>
                <option value="partial">Partial</option>
                <option value="failed">Failed</option>
                <option value="processing">Processing</option>
              </select>
            </div>
            
            <div className="text-sm text-slate-600">
              {table.getFilteredRowModel().rows.length} of {data.length} imports
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
                    <React.Fragment key={row.id}>
                      <TableRow
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
                      
                      {/* Expanded row for error details */}
                      {expandedRows.has(row.original.id) && row.original.failed_records && row.original.failed_records > 0 && (
                        <TableRow className="bg-red-50 border-l-4 border-red-200">
                          <TableCell></TableCell>
                          <TableCell colSpan={columns.length - 1}>
                            <div className="py-2">
                              <div className="flex items-center space-x-2 mb-2">
                                <AlertCircle className="h-4 w-4 text-red-600" />
                                <span className="font-medium text-red-800">Import Issues</span>
                              </div>
                              <div className="text-sm text-red-700 bg-red-100 p-3 rounded-md">
                                <p>{row.original.failed_records} records failed to import.</p>
                                <p className="mt-1 text-red-600">
                                  Check the original CSV file for formatting issues, missing required fields, or duplicate entries.
                                </p>
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={columns.length}
                      className="h-24 text-center text-slate-500"
                    >
                      <div className="flex flex-col items-center space-y-2">
                        <FileText className="h-8 w-8 text-slate-300" />
                        <p>No import history found.</p>
                        <p className="text-sm text-slate-400">Import some CSV files to see them here.</p>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>

        {/* Pagination */}
        {table.getPageCount() > 1 && (
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
        )}
      </Card>
    </div>
  )
}