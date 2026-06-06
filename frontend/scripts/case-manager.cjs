#!/usr/bin/env node

const inquirer = require('inquirer')
const fs = require('fs')
const path = require('path')

const CASES_FILE = path.join(__dirname, '../src/data/cases.json')

const CATEGORIES = [
  { value: 'ecommerce', name: '电商投流' },
  { value: 'brand', name: '品牌广告' },
  { value: 'product', name: '产品广告' },
  { value: 'drama', name: '短剧叙事' },
  { value: 'animation', name: '动画方向' },
  { value: 'film', name: '影视类' },
  { value: 'social', name: '社媒玩法' }
]

const MODELS = [
  'Seedance 2.0',
  '可灵 V1',
  '可灵 V1.5',
  'Vidu Q1',
  '自定义'
]

function loadCases() {
  const content = fs.readFileSync(CASES_FILE, 'utf-8')
  return JSON.parse(content)
}

function saveCases(cases) {
  fs.writeFileSync(CASES_FILE, JSON.stringify(cases, null, 2), 'utf-8')
}

function generateId(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')
    .replace(/^-|-$/g, '')
    + '-' + Date.now().toString(36)
}

async function addCase() {
  console.log('\n🎬 添加新案例\n')
  
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'name',
      message: '案例名称:',
      validate: (input) => input.trim() ? true : '请输入案例名称'
    },
    {
      type: 'list',
      name: 'category',
      message: '分类:',
      choices: CATEGORIES.map(c => ({ name: c.name, value: c.value }))
    },
    {
      type: 'input',
      name: 'description',
      message: '案例描述:',
      validate: (input) => input.trim() ? true : '请输入案例描述'
    },
    {
      type: 'editor',
      name: 'prompt',
      message: '提示词 (将打开编辑器):',
      validate: (input) => input.trim() ? true : '请输入提示词'
    },
    {
      type: 'input',
      name: 'negativePrompt',
      message: '负面提示词 (可选):',
      default: ''
    },
    {
      type: 'list',
      name: 'model',
      message: '推荐模型:',
      choices: MODELS
    },
    {
      type: 'input',
      name: 'size',
      message: '尺寸 (如 1080p):',
      default: '1080p'
    },
    {
      type: 'input',
      name: 'duration',
      message: '时长 (如 15秒):',
      default: '15秒'
    },
    {
      type: 'input',
      name: 'style',
      message: '风格:',
      default: ''
    },
    {
      type: 'input',
      name: 'videoUrl',
      message: '视频链接 (可选):',
      default: ''
    },
    {
      type: 'input',
      name: 'embedUrl',
      message: '嵌入链接 (可选):',
      default: ''
    },
    {
      type: 'input',
      name: 'tips',
      message: '技巧提示 (逗号分隔):',
      filter: (input) => input.split(',').map(t => t.trim()).filter(Boolean)
    },
    {
      type: 'input',
      name: 'tags',
      message: '标签 (逗号分隔):',
      filter: (input) => input.split(',').map(t => t.trim()).filter(Boolean)
    },
    {
      type: 'input',
      name: 'author',
      message: '作者 (可选):',
      default: ''
    }
  ])
  
  const newCase = {
    id: generateId(answers.name),
    name: answers.name,
    category: answers.category,
    description: answers.description,
    prompt: answers.prompt,
    negativePrompt: answers.negativePrompt || undefined,
    model: answers.model,
    parameters: {
      size: answers.size,
      duration: answers.duration,
      style: answers.style
    },
    tips: answers.tips,
    tags: answers.tags,
    author: answers.author || undefined,
    videoUrl: answers.videoUrl || undefined,
    embedUrl: answers.embedUrl || undefined
  }
  
  Object.keys(newCase).forEach(key => {
    if (newCase[key] === undefined) {
      delete newCase[key]
    }
  })
  
  const cases = loadCases()
  cases.push(newCase)
  saveCases(cases)
  
  console.log('\n✅ 案例已添加！')
  console.log(`   ID: ${newCase.id}`)
  console.log(`   名称: ${newCase.name}`)
}

async function editCase() {
  const cases = loadCases()
  
  if (cases.length === 0) {
    console.log('\n⚠️  暂无案例可编辑')
    return
  }
  
  const { caseId } = await inquirer.prompt([
    {
      type: 'list',
      name: 'caseId',
      message: '选择要编辑的案例:',
      choices: cases.map(c => ({
        name: `${c.name} (${CATEGORIES.find(cat => cat.value === c.category)?.name || c.category})`,
        value: c.id
      }))
    }
  ])
  
  const caseIndex = cases.findIndex(c => c.id === caseId)
  const currentCase = cases[caseIndex]
  
  console.log(`\n📝 编辑案例: ${currentCase.name}\n`)
  
  const answers = await inquirer.prompt([
    {
      type: 'input',
      name: 'name',
      message: '案例名称:',
      default: currentCase.name
    },
    {
      type: 'list',
      name: 'category',
      message: '分类:',
      choices: CATEGORIES.map(c => ({ name: c.name, value: c.value })),
      default: currentCase.category
    },
    {
      type: 'input',
      name: 'description',
      message: '案例描述:',
      default: currentCase.description
    },
    {
      type: 'editor',
      name: 'prompt',
      message: '提示词:',
      default: currentCase.prompt
    },
    {
      type: 'input',
      name: 'negativePrompt',
      message: '负面提示词:',
      default: currentCase.negativePrompt || ''
    },
    {
      type: 'list',
      name: 'model',
      message: '推荐模型:',
      choices: MODELS,
      default: currentCase.model
    },
    {
      type: 'input',
      name: 'size',
      message: '尺寸:',
      default: currentCase.parameters?.size || '1080p'
    },
    {
      type: 'input',
      name: 'duration',
      message: '时长:',
      default: currentCase.parameters?.duration || '15秒'
    },
    {
      type: 'input',
      name: 'style',
      message: '风格:',
      default: currentCase.parameters?.style || ''
    },
    {
      type: 'input',
      name: 'videoUrl',
      message: '视频链接:',
      default: currentCase.videoUrl || ''
    },
    {
      type: 'input',
      name: 'embedUrl',
      message: '嵌入链接:',
      default: currentCase.embedUrl || ''
    },
    {
      type: 'input',
      name: 'tips',
      message: '技巧提示 (逗号分隔):',
      default: currentCase.tips?.join(', ') || '',
      filter: (input) => input.split(',').map(t => t.trim()).filter(Boolean)
    },
    {
      type: 'input',
      name: 'tags',
      message: '标签 (逗号分隔):',
      default: currentCase.tags?.join(', ') || '',
      filter: (input) => input.split(',').map(t => t.trim()).filter(Boolean)
    },
    {
      type: 'input',
      name: 'author',
      message: '作者:',
      default: currentCase.author || ''
    }
  ])
  
  cases[caseIndex] = {
    ...currentCase,
    name: answers.name,
    category: answers.category,
    description: answers.description,
    prompt: answers.prompt,
    negativePrompt: answers.negativePrompt || undefined,
    model: answers.model,
    parameters: {
      size: answers.size,
      duration: answers.duration,
      style: answers.style
    },
    tips: answers.tips,
    tags: answers.tags,
    author: answers.author || undefined,
    videoUrl: answers.videoUrl || undefined,
    embedUrl: answers.embedUrl || undefined
  }
  
  Object.keys(cases[caseIndex]).forEach(key => {
    if (cases[caseIndex][key] === undefined) {
      delete cases[caseIndex][key]
    }
  })
  
  saveCases(cases)
  console.log('\n✅ 案例已更新！')
}

async function deleteCase() {
  const cases = loadCases()
  
  if (cases.length === 0) {
    console.log('\n⚠️  暂无案例可删除')
    return
  }
  
  const { caseId, confirm } = await inquirer.prompt([
    {
      type: 'list',
      name: 'caseId',
      message: '选择要删除的案例:',
      choices: cases.map(c => ({
        name: `${c.name} (${CATEGORIES.find(cat => cat.value === c.category)?.name || c.category})`,
        value: c.id
      }))
    },
    {
      type: 'confirm',
      name: 'confirm',
      message: '确定要删除此案例吗？',
      default: false
    }
  ])
  
  if (!confirm) {
    console.log('\n❌ 已取消删除')
    return
  }
  
  const caseIndex = cases.findIndex(c => c.id === caseId)
  const deletedCase = cases.splice(caseIndex, 1)[0]
  saveCases(cases)
  
  console.log(`\n✅ 已删除案例: ${deletedCase.name}`)
}

async function listCases() {
  const cases = loadCases()
  
  if (cases.length === 0) {
    console.log('\n⚠️  暂无案例')
    return
  }
  
  console.log('\n📋 案例列表\n')
  console.log('─'.repeat(60))
  
  cases.forEach((c, index) => {
    const categoryName = CATEGORIES.find(cat => cat.value === c.category)?.name || c.category
    console.log(`${index + 1}. ${c.name}`)
    console.log(`   分类: ${categoryName} | 模型: ${c.model}`)
    console.log(`   ID: ${c.id}`)
    console.log('─'.repeat(60))
  })
  
  console.log(`\n共 ${cases.length} 个案例\n`)
}

async function main() {
  console.log('\n🎬 案例管理工具')
  console.log('━'.repeat(40))
  
  const { action } = await inquirer.prompt([
    {
      type: 'list',
      name: 'action',
      message: '选择操作:',
      choices: [
        { name: '➕ 添加新案例', value: 'add' },
        { name: '✏️  编辑现有案例', value: 'edit' },
        { name: '🗑️  删除案例', value: 'delete' },
        { name: '📋 查看案例列表', value: 'list' },
        { name: '🚪 退出', value: 'exit' }
      ]
    }
  ])
  
  switch (action) {
    case 'add':
      await addCase()
      break
    case 'edit':
      await editCase()
      break
    case 'delete':
      await deleteCase()
      break
    case 'list':
      await listCases()
      break
    case 'exit':
      console.log('\n👋 再见！\n')
      process.exit(0)
  }
  
  const { continue: continueAction } = await inquirer.prompt([
    {
      type: 'confirm',
      name: 'continue',
      message: '继续操作？',
      default: true
    }
  ])
  
  if (continueAction) {
    await main()
  } else {
    console.log('\n👋 再见！\n')
  }
}

main().catch(console.error)
