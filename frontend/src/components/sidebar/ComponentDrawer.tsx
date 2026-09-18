import React, { useState, useMemo } from 'react';
import {
  Search,
  Plus,
  Network,
  Split,
  Globe,
  ShieldCheck,
  ShoppingCart,
  Users,
  Database,
  Zap,
  Radio,
  HardDrive,
  Laptop,
  Layers,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';
import { COMPONENT_TEMPLATES } from '../../constants/components';
import { ComponentTemplate, ComponentCategory } from '../../types/architecture';

const ICON_MAP: Record<string, React.ElementType> = {
  Network,
  Split,
  Globe,
  ShieldCheck,
  ShoppingCart,
  Users,
  Database,
  Zap,
  Radio,
  HardDrive,
  Laptop,
  Layers,
};

interface ComponentDrawerProps {
  onAddComponent: (template: ComponentTemplate) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export const ComponentDrawer: React.FC<ComponentDrawerProps> = ({
  onAddComponent,
  isOpen,
  onToggle,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'gateway', label: 'Gateways' },
    { id: 'service', label: 'Services' },
    { id: 'database', label: 'Databases' },
    { id: 'cache', label: 'Caches' },
    { id: 'queue', label: 'Queues' },
    { id: 'storage', label: 'Storage' },
    { id: 'api', label: 'Clients' },
  ];

  const filteredComponents = useMemo(() => {
    return COMPONENT_TEMPLATES.filter((comp) => {
      const matchesSearch =
        comp.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.tech.toLowerCase().includes(searchTerm.toLowerCase()) ||
        comp.description.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || comp.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [searchTerm, selectedCategory]);

  const handleDragStart = (event: React.DragEvent, template: ComponentTemplate) => {
    event.dataTransfer.setData('application/archvis-node', JSON.stringify(template));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <aside
      className={`fixed top-14 right-0 bottom-0 z-20 bg-white/95 backdrop-blur-md border-l border-slate-200 transition-all duration-300 flex ${
        isOpen ? 'w-80 shadow-xl' : 'w-0'
      }`}
    >
      {/* Toggle button on the left edge */}
      <button
        onClick={onToggle}
        title={isOpen ? 'Collapse Component Drawer' : 'Expand Component Drawer'}
        className="absolute -left-7 top-6 bg-white border border-slate-200 text-slate-600 hover:text-slate-900 rounded-l-md p-1 shadow-sm transition-colors"
      >
        {isOpen ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
      </button>

      {isOpen && (
        <div className="w-full h-full flex flex-col p-4 overflow-hidden">
          {/* Header */}
          <div className="mb-3">
            <h2 className="text-sm font-semibold text-slate-800 tracking-tight">Component Palette</h2>
            <p className="text-xs text-slate-500">Drag onto canvas or click to insert</p>
          </div>

          {/* Search bar */}
          <div className="relative mb-3">
            <Search className="w-4 h-4 text-slate-400 absolute left-2.5 top-2.5" />
            <input
              type="text"
              placeholder="Search components, tech..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white transition-all text-slate-800 placeholder-slate-400"
            />
          </div>

          {/* Category Filter Pills */}
          <div className="flex gap-1 overflow-x-auto pb-2 mb-3 scrollbar-none">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-md whitespace-nowrap transition-colors ${
                  selectedCategory === cat.id
                    ? 'bg-slate-900 text-white shadow-xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200/70'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Component List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 scrollbar-thin">
            {filteredComponents.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-400">
                No matching components found
              </div>
            ) : (
              filteredComponents.map((template) => {
                const IconComponent = ICON_MAP[template.iconName] || Database;
                return (
                  <div
                    key={template.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, template)}
                    onClick={() => onAddComponent(template)}
                    className="group border border-slate-200 hover:border-blue-400 bg-white hover:bg-blue-50/20 p-2.5 rounded-lg cursor-grab active:cursor-grabbing transition-all flex items-start justify-between gap-3 shadow-xs hover:shadow-sm"
                  >
                    <div className="flex items-start gap-2.5 overflow-hidden">
                      <div className="p-1.5 rounded-md bg-slate-100 group-hover:bg-blue-100 text-slate-600 group-hover:text-blue-600 transition-colors shrink-0 mt-0.5">
                        <IconComponent className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <h4 className="text-xs font-semibold text-slate-800 truncate group-hover:text-blue-700">
                          {template.label}
                        </h4>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-500 font-mono mt-0.5">
                          <span className="truncate">{template.tech}</span>
                          <span>•</span>
                          <span>{template.defaultCapacity.toLocaleString()} RPS</span>
                        </div>
                        <p className="text-[10px] text-slate-400 line-clamp-1 mt-1">
                          {template.description}
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      title="Add to canvas"
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-blue-100 text-blue-600 transition-opacity shrink-0"
                    >
                      <Plus className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </aside>
  );
};
