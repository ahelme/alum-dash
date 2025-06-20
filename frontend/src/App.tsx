import { AlumniDataTable } from '@/components/alumni-data-table'
import { AddAlumni } from '@/add-alumni'
import { AutomationDashboard } from '@/components/AutomationDashboard'
import { ImportHistory } from '@/components/import-history'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { GraduationCap, Users, Plus, BarChart3, Bot } from 'lucide-react'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <GraduationCap className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                AlumDash
              </h1>
              <p className="text-slate-600">Modern Alumni Achievement Tracking System with AI-Powered Discovery</p>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:grid-cols-4 mb-8">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <Bot className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="alumni" className="flex items-center gap-2">
              <Users className="h-4 w-4" />
              <span className="hidden sm:inline">Alumni</span>
            </TabsTrigger>
            <TabsTrigger value="add-alumni" className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">Add Alumni</span>
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">History</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <AutomationDashboard />
          </TabsContent>

          <TabsContent value="alumni" className="space-y-6">
            <AlumniDataTable />
          </TabsContent>

          <TabsContent value="add-alumni" className="space-y-6">
            <AddAlumni />
          </TabsContent>


          <TabsContent value="history" className="space-y-6">
            <ImportHistory />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App
