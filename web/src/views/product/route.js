import i18n from '~/i18n'
const { t } = i18n.global

const Layout = () => import('@/layout/index.vue')

export default {
  name: '商品管理',
  path: '/product',
  component: Layout,
  meta: {
    title: '商品管理',
    icon: 'uiw:shop',
    order: 2
  },
  children: [
    {
      name: '商品分类',
      path: 'category',
      component: () => import('@/views/product/category/index.vue'),
      meta: {
        title: '商品分类',
        icon: 'material-symbols:category',
        order: 1
      }
    },
    {
      name: '商品列表',
      path: 'products',
      component: () => import('@/views/product/products/index.vue'),
      meta: {
        title: '商品列表',
        icon: 'mdi:package-variant-closed',
        order: 2
      }
    }
  ]
} 