import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  Eye,
  Film,
  Globe,
  Play,
  Pause,
  RefreshCw,
  Star,
  Trophy,
  Users,
  TrendingUp,
  ExternalLink
} from 'lucide-react';

// Types matching your backend API
interface AutomationStats {
  discoveries_today: number;
  discoveries_change: number;
  high_confidence: number;
  total_discoveries: number;
  active_sources: number;
  total_sources: number;
  avg_processing_time: number;
  status: 'running' | 'stopped' | 'error';
  next_scheduled_run: string;
}

interface DataSourceStatus {
  name: string;
  type: string;
  active: boolean;
  last_run: string | null;
  next_run: string | null;
  success_rate: number;
  items_found_today: number;
  rate_limit: number;
  errors: string[];
}

interface DiscoveryItem {
  id: string;
  title: string;
  alumni_name: string;
  achievement_type: string;
  source: string;
  confidence: number;
  timestamp: string;
  source_url?: string;
  verified: boolean;
}

// WebSocket hook for real-time updates
const useWebSocket = (url: string) => {
  const [data, setData] = useState<any>(null);
  const [connectionStatus, setConnectionStatus] = useState('Connecting');

  useEffect(() => {
    const ws = new WebSocket(url);
    
    ws.onopen = () => setConnectionStatus('Connected');
    ws.onmessage = (event) => setData(JSON.parse(event.data));
    ws.onclose = () => setConnectionStatus('Disconnected');
    ws.onerror = () => setConnectionStatus('Error');

    return () => ws.close();
  }, [url]);

  return { data, connectionStatus };
};

const StatCard: React.FC<{
  title: string;
  value: string | number;
  description: string;
  trend?: string;
  isLoading?: boolean;
}> = ({ title, value, description, trend, isLoading = false }) => {
  if (isLoading) {
    return (
      <Card className="relative overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <div className="h-4 w-24 bg-muted animate-pulse rounded"></div>
        </CardHeader>
        <CardContent>
          <div className="h-8 w-16 bg-muted animate-pulse rounded mb-2"></div>
          <div className="h-3 w-32 bg-muted animate-pulse rounded"></div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="relative overflow-hidden transition-all hover:shadow-md border border-gray-200">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-foreground">{value}</div>
        <p className="text-xs text-muted-foreground mt-1">
          {description}
        </p>
        {trend && (
          <div className="flex items-center mt-2 text-xs">
            <TrendingUp className="h-3 w-3 text-gray-600 mr-1" />
            <span className="text-gray-600 font-medium">{trend}</span>
            <span className="text-muted-foreground ml-1">vs last period</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const DataSourceCard: React.FC<{
  source: DataSourceStatus;
}> = ({ source }) => {
  const getSourceIcon = (sourceName: string) => {
    const icons: Record<string, React.ComponentType<{ className?: string }>> = {
      'TMDb': Film,
      'IMDb': Film, 
      'Variety': Globe,
      'Sundance': Star,
      'AACTA': Trophy,
      'LinkedIn': Users
    };
    return icons[sourceName] || Globe;
  };

  const Icon = getSourceIcon(source.name);

  return (
    <Card className={`transition-all hover:shadow-md border ${source.active ? 'border-gray-300 bg-gray-50/50' : 'border-gray-200'}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`p-2 rounded-lg ${source.active ? 'bg-gray-100 text-gray-700' : 'bg-muted'}`}>
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm font-medium">{source.name}</CardTitle>
              <CardDescription className="text-xs">
                {source.active ? 'Active' : 'Idle'}
              </CardDescription>
            </div>
          </div>
          <div className={`w-3 h-3 rounded-full ${source.active ? 'bg-gray-500 animate-pulse' : 'bg-gray-300'}`} />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-muted-foreground">Success Rate</p>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-muted rounded-full h-2">
                <div 
                  className="bg-gray-600 h-2 rounded-full transition-all"
                  style={{ width: `${source.success_rate}%` }}
                />
              </div>
              <span className="text-xs font-medium">{source.success_rate}%</span>
            </div>
          </div>
          <div>
            <p className="text-muted-foreground">Items Found</p>
            <p className="font-semibold">{source.items_found_today}</p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
          <div>
            <p>Last Run</p>
            <p className="font-medium">
              {source.last_run ? new Date(source.last_run).toLocaleString() : 'Never'}
            </p>
          </div>
          <div>
            <p>Next Run</p>
            <p className="font-medium">
              {source.next_run ? new Date(source.next_run).toLocaleString() : 'N/A'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const RecentDiscovery: React.FC<{
  discovery: DiscoveryItem;
}> = ({ discovery }) => {
  const getAchievementIcon = (type: string) => {
    const icons: Record<string, React.ComponentType<{ className?: string }>> = {
      'Award': Trophy,
      'Festival Selection': Star,
      'Production Credit': Film,
      'Review/Reception': Eye,
      'Industry Recognition': Users
    };
    return icons[type] || Activity;
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'bg-gray-100 text-gray-800 border-gray-300';
    if (score >= 0.6) return 'bg-gray-50 text-gray-700 border-gray-200';
    return 'bg-gray-50 text-gray-600 border-gray-200';
  };

  const Icon = getAchievementIcon(discovery.achievement_type);

  return (
    <div className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
      <div className="p-2 rounded-lg bg-gray-50 text-gray-600">
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <h4 className="text-sm font-medium truncate">{discovery.title}</h4>
          <Badge className={`text-xs border ${getConfidenceColor(discovery.confidence)}`}>
            {Math.round(discovery.confidence * 100)}%
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">{discovery.alumni_name}</p>
        <div className="flex items-center justify-between mt-2">
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            <span>{discovery.source}</span>
            <span>•</span>
            <span>{new Date(discovery.timestamp).toLocaleString()}</span>
          </div>
          {discovery.source_url && (
            <Button variant="ghost" size="sm" asChild>
              <a href={discovery.source_url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-3 w-3" />
              </a>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export const AutomationDashboard: React.FC = () => {
  // State
  const [automationStats, setAutomationStats] = useState<AutomationStats | null>(null);
  const [dataSources, setDataSources] = useState<DataSourceStatus[]>([]);
  const [discoveries, setDiscoveries] = useState<DiscoveryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isAutomationRunning, setIsAutomationRunning] = useState(false);

  // WebSocket connection for real-time updates
  const { data: liveData, connectionStatus } = useWebSocket('ws://localhost:8000/ws/automation');

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        const [statsResponse, sourcesResponse, discoveriesResponse] = await Promise.all([
          fetch('/api/automation/status'),
          fetch('/api/automation/sources'),
          fetch('/api/automation/discoveries')
        ]);
        
        if (statsResponse.ok) {
          const stats = await statsResponse.json();
          setAutomationStats(stats);
          setIsAutomationRunning(stats.status === 'running');
        }
        
        if (sourcesResponse.ok) {
          const sources = await sourcesResponse.json();
          setDataSources(sources);
        }
        
        if (discoveriesResponse.ok) {
          const discoveriesData = await discoveriesResponse.json();
          setDiscoveries(discoveriesData);
        }
        
      } catch (error) {
        console.error('Error fetching automation data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle live updates
  useEffect(() => {
    if (liveData) {
      switch (liveData.type) {
        case 'new_discovery':
          setDiscoveries(prev => [liveData.discovery, ...prev.slice(0, 9)]);
          break;
        case 'status_change':
          setIsAutomationRunning(liveData.status === 'running');
          break;
      }
    }
  }, [liveData]);

  const handleToggleAutomation = async () => {
    try {
      const response = await fetch('/api/automation/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: isAutomationRunning ? 'stop' : 'start' })
      });
      
      if (response.ok) {
        setIsAutomationRunning(!isAutomationRunning);
      }
    } catch (error) {
      console.error('Error toggling automation:', error);
    }
  };

  const handleManualRun = async () => {
    try {
      const response = await fetch('/api/automation/manual-run', {
        method: 'POST'
      });
      
      if (response.ok) {
        console.log('Manual collection started');
      }
    } catch (error) {
      console.error('Error starting manual run:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Automation Dashboard</CardTitle>
              <CardDescription>
                Real-time monitoring of automated alumni achievement discovery
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${
                connectionStatus === 'Connected' 
                  ? 'bg-gray-100 text-gray-700' 
                  : 'bg-gray-100 text-gray-600'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  connectionStatus === 'Connected' ? 'bg-gray-600' : 'bg-gray-400'
                }`} />
                <span>Live Updates {connectionStatus}</span>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Discoveries Today"
          value={automationStats?.discoveries_today || 0}
          description="New achievements found"
          trend={automationStats ? `+${automationStats.discoveries_change}%` : undefined}
          isLoading={loading}
        />
        <StatCard
          title="High Confidence"
          value={automationStats?.high_confidence || 0}
          description="Verified discoveries"
          isLoading={loading}
        />
        <StatCard
          title="Active Sources"
          value={`${automationStats?.active_sources || 0}/${automationStats?.total_sources || 0}`}
          description="Data sources online"
          isLoading={loading}
        />
        <StatCard
          title="Processing Time"
          value={`${automationStats?.avg_processing_time || 0}m`}
          description="Average cycle time"
          isLoading={loading}
        />
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sources">Data Sources</TabsTrigger>
          <TabsTrigger value="discoveries">Recent Discoveries</TabsTrigger>
          <TabsTrigger value="controls">Controls</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Automation Controls */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>System Status</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${isAutomationRunning ? 'bg-gray-600' : 'bg-gray-400'}`} />
                    <span className="text-sm text-muted-foreground">
                      {isAutomationRunning ? 'Running' : 'Stopped'}
                    </span>
                  </div>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-3">
                  <Button 
                    variant={isAutomationRunning ? "destructive" : "default"}
                    onClick={handleToggleAutomation}
                    className="flex items-center space-x-2"
                  >
                    {isAutomationRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                    <span>{isAutomationRunning ? 'Pause' : 'Start'} Automation</span>
                  </Button>
                  
                  <Button variant="outline" onClick={handleManualRun}>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Manual Run
                  </Button>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Next Scheduled Run</p>
                    <p className="font-medium">
                      {automationStats?.next_scheduled_run 
                        ? new Date(automationStats.next_scheduled_run).toLocaleString() 
                        : 'Not scheduled'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Collection Interval</p>
                    <p className="font-medium">Every 6 hours</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Discoveries Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Latest Discoveries</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {discoveries.slice(0, 3).map((discovery) => (
                  <RecentDiscovery key={discovery.id} discovery={discovery} />
                ))}
                {discoveries.length === 0 && (
                  <p className="text-muted-foreground text-center py-4">
                    No discoveries yet. Start automation to begin finding achievements!
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="sources" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {dataSources.map((source, index) => (
              <DataSourceCard key={index} source={source} />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="discoveries" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>All Recent Discoveries</CardTitle>
              <CardDescription>
                Complete list of achievements found by the automation system
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {discoveries.map((discovery) => (
                <RecentDiscovery key={discovery.id} discovery={discovery} />
              ))}
              {discoveries.length === 0 && (
                <p className="text-muted-foreground text-center py-8">
                  No discoveries available yet
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="controls" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Automation Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Collection Frequency</label>
                  <select className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm">
                    <option value="6">Every 6 hours</option>
                    <option value="12">Every 12 hours</option>
                    <option value="24">Daily</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Confidence Threshold</label>
                  <Input type="number" min="0" max="100" defaultValue="70" />
                </div>
                <Button className="w-full">Save Settings</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-sm">
                  <p><strong>Status:</strong> {automationStats?.status || 'Unknown'}</p>
                  <p><strong>Uptime:</strong> 2 hours 15 minutes</p>
                  <p><strong>Last Error:</strong> None</p>
                  <p><strong>Version:</strong> 1.0.0</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};
