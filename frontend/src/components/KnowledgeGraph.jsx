import { useEffect, useMemo, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { Plus, Trash2, X } from 'lucide-react';
import { Button } from './ui/button.jsx';
import { Input } from './ui/input.jsx';

cytoscape.use(dagre);

const STYLE = [
  {
    selector: 'node',
    style: {
      'background-color': 'hsl(var(--primary))',
      label: 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'text-wrap': 'wrap',
      'text-max-width': '120px',
      'font-size': '11px',
      color: '#fff',
      width: 'label',
      height: 'label',
      padding: '12px',
      shape: 'round-rectangle',
    },
  },
  {
    selector: 'node[type="root"]',
    style: { 'background-color': 'hsl(var(--destructive))', 'font-size': '13px' },
  },
  {
    selector: 'node.hovered',
    style: { 'border-width': 2, 'border-color': '#ffd166' },
  },
  {
    selector: 'edge',
    style: {
      width: 1.5,
      'line-color': 'hsl(var(--muted-foreground))',
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'target-arrow-color': 'hsl(var(--muted-foreground))',
    },
  },
];

// Build a nested tree from flat knowledge items using their parent_id.
function buildTree(methodologyName, nodes) {
  const map = new Map();
  for (const n of nodes) {
    map.set(n.knowledge_id, {
      id: n.knowledge_id,
      label: n.concept || n.statement || 'knowledge',
      statement: n.statement || '',
      children: [],
    });
  }
  const rootChildren = [];
  for (const n of nodes) {
    const node = map.get(n.knowledge_id);
    if (!node) continue;
    if (n.parent_id && map.has(n.parent_id)) {
      map.get(n.parent_id).children.push(node);
    } else {
      rootChildren.push(node);
    }
  }
  return { id: 'root', label: methodologyName || 'Methodology', statement: '', children: rootChildren };
}

function buildElements(tree, collapsed) {
  const out = [];
  const walk = (node, parentId, hidden) => {
    if (hidden.has(node.id)) return;
    out.push({
      data: {
        id: node.id,
        label: node.label,
        statement: node.statement,
        type: node.id === 'root' ? 'root' : 'definition',
      },
    });
    if (parentId) {
      out.push({ data: { id: `${parentId}->${node.id}`, source: parentId, target: node.id } });
    }
    const childHidden = collapsed.has(node.id) ? new Set([...hidden, node.id]) : hidden;
    for (const c of node.children) {
      walk(c, node.id, childHidden);
    }
  };
  walk(tree, null, new Set());
  return out;
}

function findNode(tree, id) {
  if (tree.id === id) return tree;
  for (const c of tree.children) {
    const found = findNode(c, id);
    if (found) return found;
  }
  return null;
}

export default function KnowledgeGraph({ methodologyName, nodes = [], onAddNode, onDeleteNode }) {
  const containerRef = useRef(null);
  const [collapsed, setCollapsed] = useState(() => new Set());
  const [selectedId, setSelectedId] = useState(null);
  const [addParent, setAddParent] = useState(null);
  const [concept, setConcept] = useState('');
  const [statement, setStatement] = useState('');

  const tree = useMemo(() => buildTree(methodologyName, nodes), [methodologyName, nodes]);
  const selected = selectedId ? findNode(tree, selectedId) : null;
  const elements = useMemo(() => buildElements(tree, collapsed), [tree, collapsed]);

  useEffect(() => {
    if (!containerRef.current) return undefined;
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: STYLE,
      layout: {
        name: 'dagre',
        rankDir: 'LR',
        nodeSep: 24,
        rankSep: 70,
        edgeSep: 10,
        nodeDimensionsIncludeLabels: true,
        spacingFactor: 1.1,
        animate: true,
      },
      wheelSensitivity: 1,
      minZoom: 0.2,
      maxZoom: 3,
    });

    cy.one('layoutstop', () => cy.fit(undefined, 40));

    cy.on('tap', 'node', (e) => {
      const id = e.target.id();
      const node = findNode(tree, id);
      if (node && node.children.length) {
        setCollapsed((prev) => {
          const next = new Set(prev);
          if (next.has(id)) next.delete(id);
          else next.add(id);
          return next;
        });
      }
      setSelectedId(id);
    });
    cy.on('mouseover', 'node', (e) => e.target.addClass('hovered'));
    cy.on('mouseout', 'node', (e) => e.target.removeClass('hovered'));

    const onResize = () => cy.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      cy.destroy();
    };
  }, [elements, tree]);

  function handleAdd() {
    const label = concept.trim();
    if (!label) return;
    const parentId = addParent && addParent !== 'root' ? addParent : null;
    onAddNode?.({ parentId, concept: label, statement: statement.trim() });
    setConcept('');
    setStatement('');
    setAddParent(null);
  }

  function handleDelete(id) {
    onDeleteNode?.({ id });
    setSelectedId(null);
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div ref={containerRef} className="min-h-0 w-full flex-1 rounded-lg border bg-white" />

      {selected && (
        <div className="rounded-md bg-muted p-3 text-sm">
          <div className="flex items-center justify-between gap-2">
            <strong>{selected.label}</strong>
            <div className="flex items-center gap-1">
              {selected.id !== 'root' && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => handleDelete(selected.id)}
                  aria-label="Delete node"
                  title="Delete node"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              )}
              <Button variant="ghost" size="icon" onClick={() => setSelectedId(null)} aria-label="Close details">
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          {selected.statement && <p className="mt-1 text-muted-foreground">{selected.statement}</p>}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setAddParent(selected && selected.id !== 'root' ? selected.id : 'root')}
        >
          <Plus className="h-4 w-4" />
          {selected && selected.id !== 'root' ? `Add under "${selected.label}"` : 'Add to root'}
        </Button>

        {addParent && (
          <div className="flex w-full flex-wrap items-center gap-2">
            <Input
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
              placeholder="Concept (e.g. frequency)"
              className="min-w-[160px] flex-1"
            />
            <Input
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              placeholder="Definition / statement"
              className="min-w-[160px] flex-1"
            />
            <Button size="sm" onClick={handleAdd} disabled={!concept.trim()}>
              Save
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
