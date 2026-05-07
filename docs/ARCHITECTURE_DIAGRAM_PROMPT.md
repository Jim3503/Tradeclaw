# TradeClaw项目架构图生成Prompt

## 完整Prompt模板

```
A professional 2D flat vector academic schematic diagram (research paper style), pure white background (#FFFFFF), strictly conforming to the standard of Chinese academic dissertation/core journal illustrations, rigorous and concise logic, no commercial decorative elements, no 3D effects, no photorealistic content, pure vector infographic, crisp 4K resolution, all core text in Chinese characters.

### Global Style Specification
- Module style: Small rounded corner (radius 4px) rectangle modules, with ultra-light gray 1pt thin borders, no drop shadows, no gradients, filled only with low-saturation soft solid colors for hierarchical distinction.
- Connectors: 1pt dark gray solid arrows for main workflow, 1pt dark gray dashed arrows for feedback loop, unified arrow style, clear text labels on arrows, no redundant decoration.
- Icons: Only minimal 1pt line icons for core modules, no complex patterns, no realistic elements, no decorative designs. Icon size is much smaller than module text, with text information as the absolute core, no redundant decorative icons.
- Layout: Left-to-right main horizontal workflow, with bottom closed feedback loops, all modules aligned neatly, clear logical hierarchy.

### Module Layout & Content

1. **Top banner**: A wide rounded rectangle filled with soft blue-gray (#E8F4F8), centered text: "TradeClaw智能A股分析系统架构 (吉米仔策略室出品)", minimal line chart icon on left.

2. **Left vertical section** -- "数据采集层", stacked vertically with light pale cyan (#E6F7FF) rounded cards, connected by downward 1pt gray arrows:
   - "多源数据获取" with minimal line database icon, tiny annotation: "AkShare+东财+新浪"
   - "K线缓存系统" with minimal line cache icon
   - "实时行情API" with minimal line refresh icon
   - "持仓配置管理" with minimal line settings icon
   - "历史交易记录" with minimal line history icon
   A thick 1.5pt dark gray arrow points right from this section to the core analysis layer.

3. **Center large container** -- "CrewAI智能分析引擎", large rounded rectangle filled with soft pale purple (#F3EEFF), internally divided into 4 stacked horizontal bands:
   - **Top band**: "记忆系统", small rounded pill filled with lighter purple (#EAE4FF), 3 horizontal mini-pills: "策略记忆"+"情景记忆"+"反思记忆", with minimal line brain icon.
   - **Second band**: "数据获取Agent", rounded rectangle filled with soft purple (#ECE6FF), contains module "数据获取专家" with minimal line download icon. A 1pt upward arrow labeled"数据增强" points to memory band.
   - **Third band**: "分析Agent组", rounded rectangle filled with lavender (#E8E0FF), 2 horizontal modules: "叙事分析Agent" (minimal line text icon) and "技术分析Agent" (minimal line chart icon). A 1pt upward arrow labeled"经验参考" points from these agents to memory band.
   - **Bottom band**: "报告生成", rounded rectangle filled with light blue-purple (#E9F0FB). Left module: "报告整合Agent" with minimal line document icon; a 1pt gray arrow labeled"生成报告" points right to output module "每日A股早报" (rounded rectangle filled with soft pale green #F0F9F0), with minimal line report icon.

4. **Right vertical section** -- "智能优化层", rounded rectangle container filled with soft pale orange (#FFF4E6), with top title"自动优化系统":
   - Inside, 3 horizontally arranged small rounded pills (same pale orange fill):
     - "记忆去重" with minimal line filter icon
     - "质量提升" with minimal line arrow-up icon
     - "策略优化" with minimal line gear icon
   - Below pills, a diamond-shaped decision node (thin gray border, no fill):
     - Rightward 1pt solid green arrow labeled"保留", points to final output module"分析历史库" (rounded rectangle filled with soft pale blue #EDF4FF, with minimal line archive icon)
     - Downward 1pt solid orange arrow labeled"待改进", points to bottom feedback loop

5. **Bottom-left feedback loop** -- "K线增量更新", dashed rounded rectangle (1pt gray dashed border) filled with ultra-light gray (#F5F5F5), 2 horizontal modules:
   - "缓存检查" with minimal line search icon
   - "增量拉取" with minimal line download icon
   A curved 1pt dark gray dashed arrow flows back to top-left "多源数据获取" module, labeled"数据闭环".

6. **Bottom-right feedback loop** -- "学习优化循环", dashed rounded rectangle (1pt gray dashed border) filled with ultra-light gray (#F5F5F5), 2 horizontal modules:
   - "交易复盘" with minimal line chart icon
   - "经验提取" with minimal line lightbulb icon
   A curved 1pt dark gray dashed arrow flows back to top-center "记忆系统" band, labeled"经验学习".

7. **Bottom full-width banner**: A wide rounded rectangle filled with ultra-light gray (#F5F5F5), centered text: "数据采集 → 智能缓存 → AI分析 → 报告生成 → 历史学习 → 持续优化", minimal line cycle arrow icon on both ends.

### Module Annotations
- **Multi-source data annotation**: Add tiny text below "多源数据获取": "优先AkShare, 备用东财/新浪"
- **Memory annotation**: Add tiny text below "记忆系统": "BM25语义检索 + 自动优化"
- **Trade复盘 annotation**: Add tiny text below "交易复盘": "胜率统计 + 盈亏分析"
- **Report format annotation**: Add tiny text below "每日A股早报": "Markdown格式 + PDF导出"

### Color Palette (Low Saturation, Print-Friendly)
- Primary backgrounds: #E6F7FF (cyan), #F3EEFF (purple), #FFF4E6 (orange), #F0F9F0 (green), #EDF4FF (blue)
- Borders: #CCCCCC (1pt dark gray)
- Text: #1A1A1A (pure dark gray)
- Arrows: #666666 (medium gray)

### Final Specification
All fill colors are low-saturation soft solid colors, suitable for both color display and black-and-white printing. All text is pure dark gray for clear readability. The diagram maintains a formal academic style throughout, with no extra decorative elements, strictly following the logical structure above.
```

## 使用说明

### 1. 复制上面的完整prompt
### 2. 粘贴到AI图像生成工具（如DALL-E、Midjourney等）
### 3. 可根据需要调整颜色或细节

## 架构重点说明

该架构图展示了TradeClaw的核心特点：

1. **多源数据获取** - AkShare为主，东财/新浪为备
2. **智能K线缓存** - 增量更新，减少API调用
3. **记忆增强AI** - 历史经验检索，持续学习
4. **CrewAI多Agent** - 分工协作，专业分析
5. **自动复盘学习** - 交易统计，经验提取
6. **完整闭环** - 数据→分析→报告→学习→优化

## 输出效果

生成的架构图应该：
- ✅ 学术论文风格，严谨专业
- ✅ 逻辑清晰，层次分明
- ✅ 适合打印（灰度可读）
- ✅ 中文标注，易于理解
- ✅ 矢量格式，可缩放至4K

---

**出品方：吉米仔策略室**
