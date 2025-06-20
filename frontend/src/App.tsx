import { AlumniDataTable } from '@/components/alumni-data-table'
import { AddAlumni } from '@/add-alumni'
import { AutomationDashboard } from '@/components/AutomationDashboard'
import { ImportHistory } from '@/components/import-history'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Activity, Users, Plus, BarChart3, Bot } from 'lucide-react'

// Featured Stats Component with Gradient Numbers
const FeaturedStats = () => {
  const stats = [
    {
      number: "500+",
      title: "Alumni Tracked",
      subtitle: "Across all programs"
    },
    {
      number: "1,200+", 
      title: "Achievements Found",
      subtitle: "Awards, credits, and recognition"
    },
    {
      number: "95%",
      title: "Success Rate",
      subtitle: "Automated discovery accuracy"
    }
  ]

  return (
    <section className="w-full bg-muted/30 py-12 mb-8">
      <div className="container px-4 md:px-6">
        <div className="grid grid-cols-1 gap-8 text-center md:grid-cols-3">
          {stats.map((stat, index) => (
            <div
              key={index}
              className="group relative overflow-hidden rounded-lg bg-background/50 p-6 transition-all duration-300 hover:bg-background hover:shadow-lg"
            >
              <div className="relative z-10">
                <h3 className="text-6xl font-bold bg-gradient-to-r from-pink-600 to-blue-600 bg-clip-text text-transparent mb-4">
                  {stat.number}
                </h3>
                <p className="text-xl font-medium text-foreground mb-1">
                  {stat.title}
                </p>
                <p className="text-base text-muted-foreground">
                  {stat.subtitle}
                </p>
              </div>
              <div className="absolute inset-0 -z-10 bg-gradient-to-t from-primary/5 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function App() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="w-full bg-black text-white">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center">
              <Activity className="h-7 w-7 text-black" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">
                AlumDash
              </h1>
              <p className="text-gray-400">Modern Alumni Achievement Tracking System</p>
            </div>
          </div>
        </div>
      </header>

      {/* Featured Stats */}
      <FeaturedStats />

      {/* Main Content */}
      <div className="container mx-auto px-4 pb-8">

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
