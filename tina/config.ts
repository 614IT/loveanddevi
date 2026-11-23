import { defineConfig } from 'tinacms';

// Page content blocks — each represents a distinct Weebly-styled section.
// Order of blocks in a page == visual order on the rendered page.

const paragraphBlock = {
  name: 'paragraph',
  label: 'Paragraph (text)',
  ui: {
    defaultItem: { body: 'New paragraph. Click to edit.' },
  },
  fields: [
    {
      type: 'rich-text',
      name: 'body',
      label: 'Text',
      isBody: false,
    },
  ],
};

const headingBlock = {
  name: 'heading',
  label: 'Heading',
  ui: {
    defaultItem: { text: 'Heading', level: 'h2' },
  },
  fields: [
    { type: 'string', name: 'text', label: 'Heading text' },
    {
      type: 'string',
      name: 'level',
      label: 'Size',
      options: [
        { label: 'Large (h1)', value: 'h1' },
        { label: 'Medium (h2)', value: 'h2' },
        { label: 'Small (h3)', value: 'h3' },
      ],
    },
  ],
};

const imageBlock = {
  name: 'image',
  label: 'Image',
  ui: {
    defaultItem: { align: 'center' },
  },
  fields: [
    { type: 'image', name: 'src', label: 'Image' },
    { type: 'string', name: 'alt', label: 'Alt text (describes image)' },
    {
      type: 'string',
      name: 'align',
      label: 'Alignment',
      options: [
        { label: 'Center', value: 'center' },
        { label: 'Float left', value: 'left' },
        { label: 'Float right', value: 'right' },
      ],
    },
    { type: 'string', name: 'caption', label: 'Caption (optional)' },
  ],
};

const bulletListBlock = {
  name: 'bulletList',
  label: 'Bullet list',
  ui: {
    defaultItem: { items: ['First item', 'Second item'] },
  },
  fields: [
    {
      type: 'string',
      name: 'items',
      label: 'List items',
      list: true,
    },
  ],
};

const twoColumnBlock = {
  name: 'twoColumn',
  label: 'Two columns',
  fields: [
    {
      type: 'rich-text',
      name: 'left',
      label: 'Left column content',
    },
    {
      type: 'rich-text',
      name: 'right',
      label: 'Right column content',
    },
  ],
};

const dividerBlock = {
  name: 'divider',
  label: 'Divider (spacer / horizontal rule)',
  fields: [
    {
      type: 'string',
      name: 'style',
      label: 'Style',
      options: [
        { label: 'Thin line', value: 'line' },
        { label: 'Blank space (small)', value: 'small' },
        { label: 'Blank space (large)', value: 'large' },
      ],
    },
  ],
};

const rawHtmlBlock = {
  name: 'rawHtml',
  label: 'Raw HTML (advanced, preserves original Weebly markup)',
  ui: {
    defaultItem: { html: '<!-- paste HTML here -->' },
  },
  fields: [
    {
      type: 'string',
      name: 'html',
      label: 'HTML source',
      ui: { component: 'textarea' },
    },
  ],
};

export default defineConfig({
  branch: process.env.TINA_BRANCH || 'revamp/astro-cms',
  clientId: process.env.TINA_PUBLIC_CLIENT_ID || null,
  token: process.env.TINA_TOKEN || null,

  build: {
    outputFolder: 'admin',   // output to public/admin (coexists with Sveltia at /admin for now)
    publicFolder: 'public',
  },

  media: {
    tina: {
      mediaRoot: 'uploads/1/1/2/9/112908841',
      publicFolder: 'public',
    },
  },

  schema: {
    collections: [
      {
        name: 'page',
        label: 'Pages',
        path: 'src/content/tina-pages',
        format: 'json',
        ui: {
          router: ({ document }) => `/${document._sys.filename}`,
        },
        fields: [
          { type: 'string', name: 'title', label: 'Page title', isTitle: true, required: true },
          {
            type: 'image',
            name: 'hero_image',
            label: 'Hero background image',
            description: 'The big photo at the top of the page.',
          },
          {
            type: 'string',
            name: 'body_bg',
            label: 'Body background color (hex)',
            description: 'e.g. #db82bf for pink. Leave blank to inherit.',
          },
          {
            type: 'object',
            name: 'blocks',
            label: 'Content blocks',
            description: 'Drag the ⋮⋮ handle to reorder. Click "Add" to insert.',
            list: true,
            templates: [
              paragraphBlock,
              headingBlock,
              imageBlock,
              bulletListBlock,
              twoColumnBlock,
              dividerBlock,
              rawHtmlBlock,
            ],
          },
        ],
      },
    ],
  },
});
