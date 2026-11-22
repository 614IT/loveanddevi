import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const poems = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/poems' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date().optional(),
    image: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    date: z.coerce.date().optional(),
    image: z.string().optional(),
    excerpt: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
  schema: z.object({
    title: z.string(),
    slug: z.string().optional(),
    hero_image: z.string().optional(),
    body_bg: z.string().optional(),
    body_text: z.string().optional(),
    layout: z.enum(['default', 'wide', 'centered']).default('default'),
    show_in_nav: z.boolean().default(false),
    nav_order: z.number().optional(),
    draft: z.boolean().default(false),
  }),
});

const shop = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/shop' }),
  schema: z.object({
    title: z.string(),
    price: z.string(),
    image: z.string().optional(),
    stripe_link: z.string().url(),
    sold_out: z.boolean().default(false),
    order: z.number().default(0),
  }),
});

export const collections = { poems, blog, pages, shop };
