import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

type WhitepaperMetadata = {
  title: string;
  subtitle: string;
  publicationDate: string;
  owner: string;
  thesis: string;
};

type WhitepaperConfig = {
  repoRoot: string;
  sourceMarkdown: string;
  outputName: string;
  status: string;
  owner: string;
  coverLine: string;
  headerTitle: string;
  requiredTerms: string[];
  requiredSections: string[];
  minSections?: number;
  minPdfPages: number;
};

const forbiddenPatterns = [/sk-[A-Za-z0-9_-]+/, /OPENAI_API_KEY/, /CODEX_API_KEY/];

function run(repoRoot: string, command: string, args: string[], options: { env?: NodeJS.ProcessEnv } = {}) {
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    encoding: 'utf8',
    stdio: 'pipe',
    env: { ...process.env, ...options.env },
  });
  if (result.status !== 0) {
    throw new Error([`Command failed: ${command} ${args.join(' ')}`, result.stdout, result.stderr].filter(Boolean).join('\n'));
  }
  return result;
}

function commandPath(command: string) {
  const result = spawnSync('which', [command], { encoding: 'utf8', stdio: 'pipe' });
  return result.status === 0 ? result.stdout.trim() : null;
}

function firstMatch(markdown: string, pattern: RegExp, label: string) {
  const match = pattern.exec(markdown);
  const value = match?.[1]?.trim();
  if (!value) throw new Error(`Whitepaper Markdown is missing ${label}.`);
  return value;
}

function parseMarkdownMetadata(markdown: string, config: WhitepaperConfig): WhitepaperMetadata {
  const title = firstMatch(markdown, /^#\s+(.+)$/m, 'top-level title');
  const subtitle = firstMatch(markdown, /^>\s+(.+)$/m, 'subtitle blockquote');
  const publicationDate = firstMatch(markdown, /^发布日期：(.+)$/m, 'publication date');
  const thesis = firstMatch(markdown, /^核心判断：(.+)$/m, 'core thesis');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(publicationDate)) {
    throw new Error(`Whitepaper publication date must use YYYY-MM-DD, got ${publicationDate}.`);
  }
  for (const section of config.requiredSections) {
    if (!markdown.includes(section)) throw new Error(`Whitepaper Markdown must include ${section}.`);
  }
  const sectionCount = (markdown.match(/^##\s+/gm) ?? []).length;
  if (config.minSections && sectionCount < config.minSections) {
    throw new Error(`Whitepaper Markdown must include at least ${config.minSections} second-level sections, got ${sectionCount}.`);
  }
  return { title, subtitle, publicationDate, owner: config.owner, thesis };
}

function scanTextForSecrets(text: string) {
  const hits = forbiddenPatterns.filter((pattern) => pattern.test(text)).map(String);
  if (hits.length > 0) throw new Error(`Whitepaper text contains forbidden sensitive marker(s): ${hits.join(', ')}`);
}

function normalizePdfInlineCode(markdown: string) {
  return markdown.replace(/`([^`\n]+)`/g, '$1');
}

function stripMarkdownTitleBlock(markdown: string) {
  return markdown.replace(/^# .+\n\n> .+\n\n/, '').replace(/^## /gm, '# ').replace(/^### /gm, '## ');
}

function escapeLatexText(value: string) {
  return value
    .replace(/\\/g, '\\textbackslash{}')
    .replace(/([{}%$#&_])/g, '\\$1')
    .replace(/\^/g, '\\textasciicircum{}')
    .replace(/~/g, '\\textasciitilde{}');
}

function buildHeader(headerTitle: string) {
  return String.raw`
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\definecolor{OPLTeal}{HTML}{0F766E}
\definecolor{OPLInk}{HTML}{101828}
\definecolor{OPLMuted}{HTML}{667085}
\definecolor{OPLLine}{HTML}{D0D5DD}
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}
\setlist[itemize]{topsep=2pt,itemsep=2pt,leftmargin=18pt}
\titleformat{\section}{\Large\bfseries\color{OPLTeal}}{\thesection}{0.7em}{}
\titleformat{\subsection}{\large\bfseries\color{OPLInk}}{\thesubsection}{0.7em}{}
\titleformat{\subsubsection}{\normalsize\bfseries\color{OPLInk}}{\thesubsubsection}{0.7em}{}
\pagestyle{fancy}
\fancyhf{}
\lhead{\small\color{OPLMuted}One Person Lab}
\rhead{\small\color{OPLMuted}${escapeLatexText(headerTitle)}}
\cfoot{\small\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\renewcommand{\headrule}{\hbox to\headwidth{\color{OPLLine}\leaders\hrule height \headrulewidth\hfill}}
`;
}

function buildPdfMarkdown(metadata: WhitepaperMetadata, markdown: string, config: WhitepaperConfig) {
  const cover = [
    '\\begin{titlepage}',
    '\\thispagestyle{empty}',
    '\\vspace*{26mm}',
    '{\\color{OPLTeal}\\Large One Person Lab\\par}',
    '\\vspace{18mm}',
    `{\\Huge\\bfseries ${escapeLatexText(metadata.title)}\\par}`,
    '\\vspace{8mm}',
    `{\\LARGE ${escapeLatexText(metadata.subtitle)}\\par}`,
    '\\vspace{18mm}',
    `{\\large ${escapeLatexText(metadata.thesis)}\\par}`,
    '\\vspace{10mm}',
    `{\\large ${escapeLatexText(config.coverLine)}\\par}`,
    '\\vfill',
    `{\\large ${metadata.publicationDate}\\par}`,
    '\\vspace{4mm}',
    '{\\small Public whitepaper\\par}',
    '\\end{titlepage}',
    '\\newpage',
    '\\tableofcontents',
    '\\newpage',
    '',
  ].join('\n');
  return `${cover}${stripMarkdownTitleBlock(normalizePdfInlineCode(markdown))}`;
}

function paths(config: WhitepaperConfig) {
  const whitepaperDir = path.join(config.repoRoot, 'docs', 'site', 'latest', 'whitepapers');
  const tempDir = path.join(config.repoRoot, 'tmp', 'pdfs', config.outputName);
  return {
    sourceMarkdownPath: path.join(config.repoRoot, config.sourceMarkdown),
    generatedMarkdownPath: path.join(whitepaperDir, `${config.outputName}.md`),
    htmlPath: path.join(whitepaperDir, `${config.outputName}.html`),
    pdfPath: path.join(whitepaperDir, `${config.outputName}.pdf`),
    verificationPath: path.join(config.repoRoot, 'docs', 'delivery', 'whitepapers', `${config.outputName}-verification.json`),
    tempDir,
    tempMarkdownPath: path.join(tempDir, `${config.outputName}.pandoc.md`),
    tempHeaderPath: path.join(tempDir, `${config.outputName}-header.tex`),
    candidatePdfPath: path.join(tempDir, `${config.outputName}.candidate.pdf`),
  };
}

function buildHtml(config: WhitepaperConfig, metadata: WhitepaperMetadata, sourceMarkdownPath: string, htmlPath: string) {
  fs.mkdirSync(path.dirname(htmlPath), { recursive: true });
  run(config.repoRoot, 'pandoc', [
    sourceMarkdownPath,
    '--standalone',
    '--metadata', `title=${metadata.title}`,
    '--metadata', 'lang=zh-CN',
    '-o', htmlPath,
  ]);
}

function buildPdf(config: WhitepaperConfig, metadata: WhitepaperMetadata, markdown: string, output: ReturnType<typeof paths>) {
  fs.mkdirSync(output.tempDir, { recursive: true });
  fs.mkdirSync(path.dirname(output.pdfPath), { recursive: true });
  fs.writeFileSync(output.tempHeaderPath, buildHeader(config.headerTitle), 'utf8');
  fs.writeFileSync(output.tempMarkdownPath, buildPdfMarkdown(metadata, markdown, config), 'utf8');
  const font = process.env.OPL_WHITEPAPER_PDF_FONT || 'Noto Sans CJK SC';
  const sourceDateEpoch = String(Math.floor(new Date(`${metadata.publicationDate}T00:00:00Z`).getTime() / 1000));
  run(config.repoRoot, 'pandoc', [
    output.tempMarkdownPath,
    '--standalone',
    '--pdf-engine=xelatex',
    '--number-sections',
    '--metadata', `title-meta=${metadata.title}`,
    '--metadata', `author-meta=${metadata.owner}`,
    '--metadata', 'lang=zh-CN',
    '--include-in-header', output.tempHeaderPath,
    '-V', `mainfont=${font}`,
    '-V', `CJKmainfont=${font}`,
    '-V', 'geometry:margin=18mm',
    '-V', 'colorlinks=true',
    '-V', 'linkcolor=OPLTeal',
    '-V', 'urlcolor=OPLTeal',
    '-o', output.candidatePdfPath,
  ], { env: { SOURCE_DATE_EPOCH: sourceDateEpoch } });
  fs.copyFileSync(output.candidatePdfPath, output.pdfPath);
  fs.rmSync(output.candidatePdfPath, { force: true });
}

function parsePdfInfo(config: WhitepaperConfig, pdfFile: string) {
  const result = run(config.repoRoot, 'pdfinfo', [pdfFile]);
  const pages = Number(result.stdout.match(/^Pages:\s+(\d+)/m)?.[1] ?? 0);
  const size = result.stdout.match(/^Page size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts/m);
  return {
    raw: result.stdout,
    pages,
    page_size_pts: {
      width: Number(size?.[1] ?? 0),
      height: Number(size?.[2] ?? 0),
    },
  };
}

function renderPdf(config: WhitepaperConfig, pdfFile: string, renderDir: string) {
  fs.rmSync(renderDir, { recursive: true, force: true });
  fs.mkdirSync(renderDir, { recursive: true });
  run(config.repoRoot, 'pdftoppm', ['-png', '-r', '120', pdfFile, path.join(renderDir, 'page')]);
  return { renderDir, pages: fs.readdirSync(renderDir).filter((name) => name.endsWith('.png')).sort() };
}

function extractPdfText(config: WhitepaperConfig, pdfFile: string) {
  return run(config.repoRoot, 'pdftotext', [pdfFile, '-']).stdout;
}

function fileSha1(filePath: string) {
  return crypto.createHash('sha1').update(fs.readFileSync(filePath)).digest('hex');
}

function parseMarkdownLinks(markdown: string) {
  return [...markdown.matchAll(/- \[([^\]]+)\]\(([^)]+)\)：(.+)/g)].map((match) => ({
    label: match[1],
    url: match[2],
    note: match[3],
  }));
}

function relativeToRepo(config: WhitepaperConfig, filePath: string) {
  return path.relative(config.repoRoot, filePath);
}

export function buildOplWhitepaper(config: WhitepaperConfig) {
  const output = paths(config);
  fs.mkdirSync(path.dirname(output.htmlPath), { recursive: true });
  const markdown = fs.readFileSync(output.sourceMarkdownPath, 'utf8');
  const metadata = parseMarkdownMetadata(markdown, config);
  scanTextForSecrets(markdown);
  buildHtml(config, metadata, output.sourceMarkdownPath, output.htmlPath);
  buildPdf(config, metadata, markdown, output);

  const render = renderPdf(config, output.pdfPath, path.join(output.tempDir, 'rendered'));
  const info = parsePdfInfo(config, output.pdfPath);
  if (info.pages < config.minPdfPages) {
    throw new Error(`Expected whitepaper PDF to have at least ${config.minPdfPages} pages, got ${info.pages}.`);
  }
  if (info.page_size_pts.height <= info.page_size_pts.width) {
    throw new Error(`Expected portrait PDF, got ${info.page_size_pts.width}x${info.page_size_pts.height} pts.`);
  }

  const rawText = extractPdfText(config, output.pdfPath);
  const text = rawText.replace(/[\u2010-\u2015]/g, '-');
  const missingTerms = config.requiredTerms.filter((term) => !text.includes(term));
  if (missingTerms.length > 0) throw new Error(`Generated PDF text is missing required terms: ${missingTerms.join(', ')}`);

  const verification = {
    status: config.status,
    generated_at: `${metadata.publicationDate}T00:00:00.000Z`,
    source_markdown: relativeToRepo(config, output.sourceMarkdownPath),
    generated_markdown: relativeToRepo(config, output.generatedMarkdownPath),
    generated_html: relativeToRepo(config, output.htmlPath),
    generated_pdf: relativeToRepo(config, output.pdfPath),
    temp_markdown: relativeToRepo(config, output.tempMarkdownPath),
    rendered_dir: relativeToRepo(config, render.renderDir),
    rendered_pages: render.pages.length,
    rendered_page_hashes: render.pages.map((page) => ({ page, sha1: fileSha1(path.join(render.renderDir, page)) })),
    pdf_pages: info.pages,
    pdf_page_size_pts: info.page_size_pts,
    required_terms: config.requiredTerms,
    required_terms_status: 'present',
    style_profile: 'opl-whitepaper-pandoc-xelatex-v1',
    tools: {
      pandoc: commandPath('pandoc'),
      xelatex: commandPath('xelatex'),
      pdfinfo: commandPath('pdfinfo'),
      pdftoppm: commandPath('pdftoppm'),
      pdftotext: commandPath('pdftotext'),
    },
    references: parseMarkdownLinks(markdown),
  };

  fs.copyFileSync(output.sourceMarkdownPath, output.generatedMarkdownPath);
  fs.mkdirSync(path.dirname(output.verificationPath), { recursive: true });
  fs.writeFileSync(output.verificationPath, `${JSON.stringify(verification, null, 2)}\n`, 'utf8');
  console.log(JSON.stringify(verification, null, 2));
}
