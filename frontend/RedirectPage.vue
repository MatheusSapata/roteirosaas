<template>
  <div class="min-h-screen flex items-center justify-center bg-white px-4">
    <div class="text-center">
      <h1 class="text-xl font-semibold text-slate-900">Redirecionando...</h1>
      <p class="mt-2 text-sm text-slate-500">Aguarde um instante.</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const redirects = {
  profissionalmensal: 'https://pay.cakto.com.br/7o7zrup_800651',
  profissionalanual: 'https://pay.cakto.com.br/nxc42uz',
  agenciamensal: 'https://pay.cakto.com.br/n7vnc73_800688',
  agenciaanual: 'https://pay.cakto.com.br/32uvp8b',
  escalamensal: 'https://pay.cakto.com.br/iexkakw_800692',
  escalaanual: 'https://pay.cakto.com.br/pxzgp5s',
}

onMounted(() => {
  const slug = route.params.slug
  const target = redirects[slug]

  if (target) {
    window.location.href = target
  } else {
    window.location.href = '/'
  }
})
</script>