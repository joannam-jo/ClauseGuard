import React from 'react';
import { Link } from 'react-router-dom';
import { FileText, Shield, MessageSquare, BarChart3, ArrowRight, CheckCircle } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';

export default function Home() {
  const features = [
    {
      icon: FileText,
      title: 'PDF Analysis',
      description: 'Upload any finance agreement PDF and get instant clause extraction with AI-powered analysis.',
    },
    {
      icon: Shield,
      title: 'Risk Detection',
      description: 'Automatically identify harmful clauses like hidden fees, penalty rates, and unfair terms.',
    },
    {
      icon: MessageSquare,
      title: 'Document Chat',
      description: 'Ask questions about your document and get grounded answers from the agreement text.',
    },
    {
      icon: BarChart3,
      title: 'ML-Powered Scoring',
      description: 'Get an overall risk score powered by trained machine learning models.',
    },
  ];

  const steps = [
    { step: '1', title: 'Upload', description: 'Drop your PDF agreement' },
    { step: '2', title: 'Analyze', description: 'AI extracts and evaluates clauses' },
    { step: '3', title: 'Review', description: 'See risks and get recommendations' },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden hero-gradient">
        <div className="px-4 sm:px-6 lg:px-8 py-20 sm:py-32">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight mb-6">
              Finance Agreement
              <span className="text-primary block">Analyzer</span>
            </h1>
            <p className="text-lg sm:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Upload your loan, lease, or credit card agreement. Our RAG-based AI analyzes every clause,
              identifies risks, and helps you make informed decisions.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/upload">
                <Button size="lg" className="rounded-lg px-8" data-testid="home-upload-cta-button">
                  Analyze Agreement
                  <ArrowRight className="ml-2 w-4 h-4" />
                </Button>
              </Link>
              <Link to="/dashboard">
                <Button variant="outline" size="lg" className="rounded-lg px-8">
                  View Dashboard
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Steps Section */}
      <section className="py-16 bg-muted/30">
        <div className="px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {steps.map((item) => (
              <div key={item.step} className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xl font-bold">
                  {item.step}
                </div>
                <div>
                  <h3 className="font-semibold">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto">
          <h2 className="text-3xl font-semibold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {features.map((feature) => (
              <Card key={feature.title} className="card-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-lg bg-primary/10">
                      <feature.icon className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
                      <p className="text-muted-foreground">{feature.description}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* What We Detect Section */}
      <section className="py-20 bg-muted/30">
        <div className="px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto">
          <h2 className="text-3xl font-semibold text-center mb-12">What We Detect</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-red-500 mb-4 flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Harmful Clauses
              </h3>
              <ul className="space-y-2">
                {[
                  'Penalty rates > 3%/month',
                  'Unilateral modification rights',
                  'Auto-renewal without notice',
                  'Hidden fees',
                  'Biased arbitration',
                  'Acceleration without grace',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-green-500 mb-4 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Beneficial Clauses
              </h3>
              <ul className="space-y-2">
                {[
                  'Fair interest rates',
                  'Grace periods',
                  'No prepayment penalty',
                  'Transparent fees',
                  'Right to cure defaults',
                  'Consumer protections',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span className="w-1.5 h-1.5 rounded-full bg-green-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="py-12 border-t">
        <div className="px-4 sm:px-6 lg:px-8 max-w-3xl mx-auto text-center">
          <p className="text-sm text-muted-foreground">
            <strong>Academic Project Disclaimer:</strong> This tool uses machine learning models
            for educational purposes. Model outputs are probabilistic and may be incomplete.
            Always consult a legal professional for important financial decisions.
          </p>
        </div>
      </section>
    </div>
  );
}
