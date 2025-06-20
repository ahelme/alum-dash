import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  UserPlus, 
  CheckCircle2, 
  XCircle,
  Loader2,
  User,
  Mail,
  Globe,
  Calendar,
  GraduationCap
} from 'lucide-react';

interface AlumniFormData {
  name: string;
  graduation_year: string;
  degree_program: string;
  email: string;
  linkedin_url: string;
  imdb_url: string;
  website: string;
}

interface FormMessage {
  type: 'success' | 'error';
  text: string;
}

const degreePrograms = [
  'Film Production',
  'Screenwriting', 
  'Animation',
  'Documentary',
  'Television'
];

export const AddAlumni: React.FC = () => {
  const [formData, setFormData] = useState<AlumniFormData>({
    name: '',
    graduation_year: '',
    degree_program: '',
    email: '',
    linkedin_url: '',
    imdb_url: '',
    website: ''
  });
  
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<FormMessage | null>(null);

  const handleInputChange = (field: keyof AlumniFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    // Clear message when user starts typing
    if (message) setMessage(null);
  };

  const validateForm = (): string[] => {
    const errors: string[] = [];
    
    if (!formData.name.trim()) {
      errors.push('Name is required');
    }
    
    if (!formData.graduation_year) {
      errors.push('Graduation year is required');
    } else {
      const year = parseInt(formData.graduation_year);
      if (isNaN(year) || year < 1970 || year > 2030) {
        errors.push('Graduation year must be between 1970 and 2030');
      }
    }
    
    if (!formData.degree_program) {
      errors.push('Degree program is required');
    }
    
    if (formData.email && !formData.email.includes('@')) {
      errors.push('Please enter a valid email address');
    }
    
    // Validate URLs if provided
    const urlFields = [
      { field: 'linkedin_url', name: 'LinkedIn URL' },
      { field: 'imdb_url', name: 'IMDb URL' },
      { field: 'website', name: 'Website URL' }
    ];
    
    urlFields.forEach(({ field, name }) => {
      const url = formData[field as keyof AlumniFormData];
      if (url && !url.startsWith('http://') && !url.startsWith('https://')) {
        errors.push(`${name} must start with http:// or https://`);
      }
    });
    
    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const errors = validateForm();
    if (errors.length > 0) {
      setMessage({
        type: 'error',
        text: errors.join(', ')
      });
      return;
    }

    setSubmitting(true);
    
    try {
      // Prepare data for submission
      const submitData = {
        name: formData.name.trim(),
        graduation_year: parseInt(formData.graduation_year),
        degree_program: formData.degree_program,
        email: formData.email.trim() || null,
        linkedin_url: formData.linkedin_url.trim() || null,
        imdb_url: formData.imdb_url.trim() || null,
        website: formData.website.trim() || null
      };
      
      const response = await fetch('/api/alumni', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(submitData)
      });
      
      if (response.ok) {
        setMessage({
          type: 'success',
          text: 'Alumni added successfully!'
        });
        
        // Reset form
        setFormData({
          name: '',
          graduation_year: '',
          degree_program: '',
          email: '',
          linkedin_url: '',
          imdb_url: '',
          website: ''
        });
      } else {
        const errorData = await response.json();
        setMessage({
          type: 'error',
          text: errorData.detail || 'Failed to add alumni'
        });
      }
    } catch (error) {
      console.error('Error adding alumni:', error);
      setMessage({
        type: 'error',
        text: 'Error adding alumni. Please try again.'
      });
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      graduation_year: '',
      degree_program: '',
      email: '',
      linkedin_url: '',
      imdb_url: '',
      website: ''
    });
    setMessage(null);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Add New Alumni</h2>
        <p className="text-muted-foreground">
          Register a new graduate in the alumni tracking system
        </p>
      </div>

      {/* Message Display */}
      {message && (
        <div className={`p-4 rounded-lg border ${
          message.type === 'success' 
            ? 'bg-green-50 text-green-800 border-green-200' 
            : 'bg-red-50 text-red-800 border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            {message.type === 'success' ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <XCircle className="h-5 w-5" />
            )}
            <span>{message.text}</span>
          </div>
        </div>
      )}

      {/* Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <UserPlus className="h-5 w-5" />
            <span>Alumni Information</span>
          </CardTitle>
          <CardDescription>
            Please fill out all required fields marked with *
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Required Fields */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Required Information</span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Full Name *
                  </label>
                  <Input
                    type="text"
                    value={formData.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Enter full name"
                    maxLength={100}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Graduation Year *
                  </label>
                  <Input
                    type="number"
                    value={formData.graduation_year}
                    onChange={(e) => handleInputChange('graduation_year', e.target.value)}
                    placeholder="2020"
                    min="1970"
                    max="2030"
                    required
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Degree Program *
                </label>
                <select
                  value={formData.degree_program}
                  onChange={(e) => handleInputChange('degree_program', e.target.value)}
                  className="w-full px-3 py-2 border border-input bg-background rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  required
                >
                  <option value="">Select a degree program</option>
                  {degreePrograms.map(program => (
                    <option key={program} value={program}>{program}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Optional Fields */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <Mail className="h-5 w-5" />
                <span>Contact Information</span>
                <Badge variant="secondary" className="ml-2">Optional</Badge>
              </h3>
              
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Email Address
                </label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  placeholder="email@example.com"
                />
              </div>
            </div>

            {/* Social Links */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <Globe className="h-5 w-5" />
                <span>Professional Links</span>
                <Badge variant="secondary" className="ml-2">Optional</Badge>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    LinkedIn URL
                  </label>
                  <Input
                    type="url"
                    value={formData.linkedin_url}
                    onChange={(e) => handleInputChange('linkedin_url', e.target.value)}
                    placeholder="https://linkedin.com/in/username"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    IMDb URL
                  </label>
                  <Input
                    type="url"
                    value={formData.imdb_url}
                    onChange={(e) => handleInputChange('imdb_url', e.target.value)}
                    placeholder="https://www.imdb.com/name/nm1234567"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Personal Website
                  </label>
                  <Input
                    type="url"
                    value={formData.website}
                    onChange={(e) => handleInputChange('website', e.target.value)}
                    placeholder="https://example.com"
                  />
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-4 pt-4">
              <Button 
                type="submit" 
                disabled={submitting}
                className="flex items-center space-x-2"
              >
                {submitting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <UserPlus className="h-4 w-4" />
                )}
                <span>{submitting ? 'Adding Alumni...' : 'Add Alumni'}</span>
              </Button>
              
              <Button 
                type="button" 
                variant="outline"
                onClick={resetForm}
                disabled={submitting}
              >
                Reset Form
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};
