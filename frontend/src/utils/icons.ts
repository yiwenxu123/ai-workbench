/**
 * 图标映射与动态渲染工具
 * 统一使用 lucide-vue-next 图标替换 Emoji
 */

import type { Component } from 'vue'

// ============================================================
// 1. Emoji → Lucide 图标名称映射（用于 data 文件中的 icon 字段）
// ============================================================
export const emojiToLucideMap: Record<string, string> = {
  // 通用
  '✦': 'Sparkles',
  '✨': 'Sparkles',
  '⭐': 'Star',
  '✅': 'CheckCircle',
  '✓': 'Check',
  '💡': 'Lightbulb',
  '⚠️': 'AlertTriangle',
  '🚫': 'Ban',
  '🔄': 'RefreshCw',
  '💾': 'Save',
  '📌': 'Pin',
  '🆕': 'PlusCircle',

  // 文件/编辑
  '📝': 'FileText',
  '✏️': 'Pencil',
  '🖌️': 'Brush',
  '📋': 'ClipboardList',
  '📄': 'FileText',
  '📑': 'Files',

  // 图片/媒体
  '🖼️': 'Image',
  '🎬': 'Film',
  '📷': 'Camera',
  '📹': 'Video',
  '📺': 'Monitor',
  '🖥️': 'Monitor',
  '📼': 'Disc',

  // 工具/设置
  '⚙️': 'Settings',
  '🔧': 'Wrench',
  '🔌': 'Plug',
  '🤖': 'Bot',

  // 导航/方向
  '➡️': 'ArrowRight',
  '⬅️': 'ArrowLeft',
  '⬆️': 'ArrowUp',
  '⬇️': 'ArrowDown',
  '↗️': 'ArrowUpRight',

  // 搜索/分析
  '🔍': 'Search',
  '👁️': 'Eye',
  '👀': 'Eye',
  '🔮': 'Scan',
  '📊': 'BarChart3',

  // 知识/学习
  '📚': 'BookOpen',
  '📖': 'BookOpen',
  '🎓': 'GraduationCap',
  '🏢': 'Building2',

  // 人物
  '👤': 'User',
  '🧍': 'User',
  '🗣️': 'MessageSquare',
  '🏃': 'User',

  // 场景/物体
  '📦': 'Package',
  '🛒': 'ShoppingCart',
  '🏔️': 'Mountain',
  '🏛️': 'Landmark',
  '🏞️': 'Mountain',
  '🍽️': 'UtensilsCrossed',
  '🎨': 'Palette',
  '📱': 'Smartphone',
  '📣': 'Megaphone',
  '🎯': 'Target',
  '🎉': 'PartyPopper',
  '🧧': 'Gift',
  '🏮': 'Lantern',
  '🐲': 'Sparkles',
  '🌕': 'Moon',
  '🇨🇳': 'Flag',
  '🎄': 'TreePine',
  '🎆': 'Sparkles',
  '🛍️': 'ShoppingBag',
  '🌀': 'CircleDot',

  // 艺术/风格
  '🎭': 'Theater',
  '🎥': 'Clapperboard',

  // 其他
  '📐': 'Ruler',
  '⚡': 'Zap',
  '🧪': 'FlaskConical',
  '🌙': 'Moon',
  '🧱': 'BrickWall',
  '🌈': 'Rainbow',
  '📢': 'Megaphone',
}

// ============================================================
// 2. 获取 Lucide 图标名称
// ============================================================
export function getLucideIconName(emoji: string): string {
  return emojiToLucideMap[emoji] || 'Circle'
}

// ============================================================
// 3. 动态加载 lucide-vue-next 图标组件
// ============================================================
import * as LucideIcons from 'lucide-vue-next'

export function getLucideIconComponent(name: string): Component {
  const component = (LucideIcons as unknown as Record<string, Component>)[name]
  return component || LucideIcons.Circle
}

// ============================================================
// 4. 常用 Lucide 图标名称常量（用于组件中直接引用）
// ============================================================
export const LucideIconNames = {
  // 导航
  Compass: 'Compass',
  Image: 'Image',
  Film: 'Film',
  ColorWand: 'Wand2',

  // 右侧面板
  Library: 'Library',
  BookOpen: 'BookOpen',
  Scan: 'Scan',
  Images: 'Images',
  DocumentText: 'FileText',
  CloudDownload: 'DownloadCloud',

  // 通用操作
  Settings: 'Settings',
  Grid: 'LayoutGrid',
  Close: 'X',
  Sparkles: 'Sparkles',
  Star: 'Star',
  Check: 'Check',
  CheckCircle: 'CheckCircle',
  Lightbulb: 'Lightbulb',
  AlertTriangle: 'AlertTriangle',
  Ban: 'Ban',
  RefreshCw: 'RefreshCw',
  Save: 'Save',
  Pin: 'Pin',
  PlusCircle: 'PlusCircle',

  // 文件编辑
  FileText: 'FileText',
  Pencil: 'Pencil',
  Brush: 'Brush',
  ClipboardList: 'ClipboardList',

  // 媒体
  Camera: 'Camera',
  Video: 'Video',
  Monitor: 'Monitor',
  Disc: 'Disc',

  // 工具
  Wrench: 'Wrench',
  Plug: 'Plug',
  Bot: 'Bot',

  // 搜索分析
  Search: 'Search',
  Eye: 'Eye',
  BarChart3: 'BarChart3',

  // 知识
  Building2: 'Building2',
  User: 'User',
  MessageSquare: 'MessageSquare',

  // 场景
  Package: 'Package',
  ShoppingCart: 'ShoppingCart',
  Mountain: 'Mountain',
  Landmark: 'Landmark',
  UtensilsCrossed: 'UtensilsCrossed',
  Palette: 'Palette',
  Smartphone: 'Smartphone',
  Megaphone: 'Megaphone',
  Target: 'Target',
  PartyPopper: 'PartyPopper',
  Gift: 'Gift',
  Flag: 'Flag',
  TreePine: 'TreePine',
  Theater: 'Theater',
  Clapperboard: 'Clapperboard',
  Ruler: 'Ruler',
  Zap: 'Zap',
  FlaskConical: 'FlaskConical',
  Moon: 'Moon',
  ShoppingBag: 'ShoppingBag',
  CircleDot: 'CircleDot',
  Brain: 'Brain',
  DownloadCloud: 'DownloadCloud',
  LayoutGrid: 'LayoutGrid',
  X: 'X',
  Wand2: 'Wand2',
  BrickWall: 'BrickWall',
  Rainbow: 'Rainbow',
} as const

export type LucideIconName = typeof LucideIconNames[keyof typeof LucideIconNames]
