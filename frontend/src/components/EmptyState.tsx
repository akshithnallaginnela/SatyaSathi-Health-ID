import React from 'react';
import { Activity, FileText, Heart, TrendingUp } from 'lucide-react';

interface EmptyStateProps {
  type: 'vitals' | 'reports' | 'tasks' | 'trends';
  onAction?: () => void;
  actionText?: string;
}

export default function EmptyState({ type, onAction, actionText }: EmptyStateProps) {
  const configs = {
    vitals: {
      icon: Activity,
      title: 'No Vitals Logged Yet',
      description: 'Start tracking your BP, sugar, and BMI to get personalized health insights.',
      illustration: '🩺',
      color: 'bg-blue-50',
      iconColor: 'text-blue-500',
      buttonColor: 'bg-blue-500',
    },
    reports: {
      icon: FileText,
      title: 'No Blood Reports',
      description: 'Upload your blood report to get AI-powered analysis and daily health tasks.',
      illustration: '📋',
      color: 'bg-purple-50',
      iconColor: 'text-purple-500',
      buttonColor: 'bg-purple-500',
    },
    tasks: {
      icon: Heart,
      title: 'No Tasks Yet',
      description: 'Log your vitals or upload a report to get personalized daily health tasks.',
      illustration: '✅',
      color: 'bg-green-50',
      iconColor: 'text-green-500',
      buttonColor: 'bg-green-500',
    },
    trends: {
      icon: TrendingUp,
      title: 'Not Enough Data',
      description: 'Keep logging your vitals regularly to see trends and track your progress.',
      illustration: '📈',
      color: 'bg-orange-50',
      iconColor: 'text-orange-500',
      buttonColor: 'bg-orange-500',
    },
  };

  const config = configs[type];
  const Icon = config.icon;

  return (
    <div className={`${config.color} rounded-3xl p-8 text-center border-2 border-dashed border-gray-200`}>
      <div className="text-6xl mb-4 animate-bounce">{config.illustration}</div>
      <div className={`w-16 h-16 ${config.color} rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-white shadow-sm`}>
        <Icon size={32} className={config.iconColor} />
      </div>
      <h3 className="text-dark-teal font-extrabold text-lg mb-2">{config.title}</h3>
      <p className="text-muted-teal text-sm leading-relaxed mb-6 max-w-xs mx-auto">
        {config.description}
      </p>
      {onAction && (
        <button
          onClick={onAction}
          className={`${config.buttonColor} text-white font-extrabold px-6 py-3 rounded-2xl shadow-md hover:shadow-lg transition-all`}
        >
          {actionText || 'Get Started'}
        </button>
      )}
    </div>
  );
}
