<template>
  <div
    :class="[
      'min-h-screen overflow-x-hidden text-[14px] md:h-screen md:overflow-hidden',
      isDarkTheme ? 'bg-[#05070f] text-slate-100' : 'bg-slate-50 text-slate-900',
      themeWrapperClass
    ]"
  >
    <div v-if="showAuthSplash" class="flex min-h-screen items-center justify-center md:h-screen">
      <div class="flex flex-col items-center gap-4">
        <div
          :class="[
            'h-12 w-12 animate-spin rounded-full border-4 border-transparent',
            isDarkTheme ? 'border-t-white border-r-white/40' : 'border-t-brand border-r-brand/35'
          ]"
        ></div>
      </div>
    </div>
    <template v-else>
    <div class="flex min-h-screen md:h-screen">
      <aside
        :class="[
          'admin-sidebar hidden w-[246px] flex-shrink-0 flex-col justify-between border-r px-0 py-6 shadow-md md:fixed md:inset-y-0 md:left-0 md:flex',
          'border-[#254d32] bg-[#1A3D25] text-slate-100'
        ]"
      >
        <div class="flex flex-1 flex-col overflow-y-auto px-6">
          <div class="mb-4 flex items-center justify-center">
            <img :src="sidebarLogoSrc" alt="Roteiro Online" class="max-h-[4.4rem] object-contain md:max-h-16" />
          </div>
          <nav class="flex-1 space-y-2">
            <section
              v-for="section in sidebarSections"
              :key="`desktop-section-${section.id}`"
              class="pt-1 first:pt-0"
              :class="section.id !== sidebarSections[0]?.id ? 'mt-2' : ''"
            >
              <p class="px-2 pb-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white/35">{{ section.label }}</p>
              <div class="space-y-1">
                <template v-for="item in section.items" :key="item.id">
              <RouterLink
                v-if="item.type === 'link'"
                :to="item.to"
                class="flex items-center gap-2 rounded-xl px-3 py-2 text-[13px] font-medium transition"
                :class="isTopLevelActive(item) ? activeClass : inactiveClass"
              >
                <span
                  :class="[
                    'flex h-6 w-6 items-center justify-center rounded-full',
                    'bg-white/10 text-slate-100'
                  ]"
                >
                  <svg
                    :viewBox="navIconViewBoxes[item.iconPath] || navIconViewBoxes.default"
                    :class="['h-4 w-4', navIconSizes[item.iconPath]]"
                    :stroke-width="navIconStrokeWidths[item.iconPath] || null"
                    v-html="navIcons[item.iconPath] || navIcons.default"
                  ></svg>
                </span>
                <span class="flex-1">{{ item.label }}</span>
                <span
                  v-if="getNavBadge(item.id) !== null"
                  class="rounded-full bg-[#3DCC5F] px-2 py-0.5 text-[10px] font-bold leading-none text-[#0F1F14]"
                >
                  {{ getNavBadge(item.id) }}
                </span>
              </RouterLink>
              <div v-else class="space-y-1">
                <button
                  type="button"
                  class="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-[13px] font-medium transition"
                  :class="isParentActive(item) ? activeClass : inactiveClass"
                  @click="toggleNavGroup(item.id)"
                >
                  <span
                    :class="[
                      'flex h-6 w-6 items-center justify-center rounded-full',
                      'bg-white/10 text-slate-100'
                    ]"
                  >
                    <svg
                      :viewBox="navIconViewBoxes[item.iconPath] || navIconViewBoxes.default"
                      :class="['h-4 w-4', navIconSizes[item.iconPath]]"
                      :stroke-width="navIconStrokeWidths[item.iconPath] || null"
                      v-html="navIcons[item.iconPath] || navIcons.default"
                    ></svg>
                  </span>
                  <span class="flex-1 text-left">{{ item.label }}</span>
                  <svg
                    viewBox="0 0 24 24"
                    class="mr-1 h-4 w-4 transition-transform"
                    :class="isGroupExpanded(item) ? 'rotate-180' : ''"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                  <span
                    v-if="getNavBadge(item.id) !== null"
                    class="rounded-full bg-[#3DCC5F] px-2 py-0.5 text-[10px] font-bold leading-none text-[#0F1F14]"
                  >
                    {{ getNavBadge(item.id) }}
                  </span>
                </button>
                <div v-if="isGroupExpanded(item)" class="ml-8 space-y-1 pb-1">
                  <RouterLink
                    v-for="child in item.children"
                    :key="`${item.id}-${child.path}`"
                    :to="child.path"
                    class="flex items-center rounded-lg px-3 py-1.5 text-[12px] font-medium transition"
                    :class="isChildActive(child.path) ? childActiveClass : childInactiveClass"
                  >
                    <span>{{ child.label }}</span>
                  </RouterLink>
                </div>
              </div>
                </template>
              </div>
            </section>
          </nav>
        </div>

        <div
          :class="[
            'mt-8 border-t px-6 pt-4 space-y-3',
            'border-slate-800'
          ]"
        >
          <button
            type="button"
            class="flex w-full items-center justify-between rounded-xl border px-4 py-3 text-sm font-semibold transition"
            :class="isDarkTheme ? 'border-white/15 bg-white/5 text-white hover:bg-white/10' : 'border-white/15 bg-white/5 text-white hover:bg-white/10'"
            @click="toggleTheme"
          >
            <div class="text-left">
              <p class="text-sm font-semibold leading-tight">{{ viewCopy.themeToggle.title }}</p>
              <p class="text-xs opacity-70">{{ isDarkTheme ? viewCopy.themeToggle.active : viewCopy.themeToggle.inactive }}</p>
            </div>
            <span
              :class="[
                'relative inline-flex h-6 w-11 items-center rounded-full transition',
                isDarkTheme ? 'bg-[#3DCC5F]' : 'bg-white/40'
              ]"
            >
              <span
                :class="[
                  'inline-block h-5 w-5 rounded-full bg-white shadow transition toggle-knob',
                  isDarkTheme ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
            </span>
          </button>
          <button
            type="button"
            @click="handleLogout"
            class="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition"
            :class="isDarkTheme ? 'text-white hover:bg-white/10' : 'text-white/90 hover:bg-white/10'"
          >
            <span class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-[#3DCC5F] text-sm font-extrabold text-[#0F1F14]">
              {{ userInitial }}
            </span>
            <span class="min-w-0 flex-1">
              <span class="block truncate text-[13px] font-semibold text-white">{{ userDisplayName }}</span>
              <span class="block text-[11px] text-white/50">{{ userRoleLabel }}</span>
            </span>
            <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-white/80">
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                <path d="M15 17l5-5-5-5" />
                <path d="M20 12H9" />
                <path d="M12 19H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6" />
              </svg>
            </span>
          </button>
        </div>
      </aside>
      <main :class="['admin-main flex min-h-0 flex-1 flex-col overflow-x-hidden md:ml-[246px]',isDarkTheme ? 'bg-[#05070f] text-slate-100' : 'bg-slate-50 text-slate-900']">
        <div
          :class="[
            'admin-content flex-1 min-h-0 overflow-y-auto overflow-x-hidden px-3 pt-1 pb-4 md:px-6 md:pt-2 md:pb-6',
            isDarkTheme ? 'text-slate-100' : 'text-slate-900'
          ]"
        >
          <div v-if="isMobileViewport" :class="['mb-2 flex items-center justify-end gap-3', pageTitleRowPaddingClass]">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-full p-2 transition"
              :class="isDarkTheme ? 'text-white hover:bg-white/5' : 'text-slate-700 hover:bg-slate-100'"
              @click="mobileMenuOpen = true"
            >
              <span class="sr-only">{{ viewCopy.sidebar.openMenu }}</span>
              <svg viewBox="0 0 24 24" class="h-7 w-7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
          <RouterView />
        </div>
      </main>
    </div>
    </template>

    <transition name="fade">
        <div
          v-if="mobileMenuOpen"
          class="fixed inset-0 z-40 flex justify-end md:hidden"
        >
        <div
          class="flex-1"
          :class="'bg-slate-900/65'"
          @click="mobileMenuOpen = false"
        ></div>
        <div
          class="w-72 max-w-full p-5 shadow-2xl transition-colors md:rounded-l-3xl"
          :class="'bg-[#1A3D25] text-slate-100'"
        >
          <div class="mb-6 flex items-center justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.3em]" :class="isDarkTheme ? 'text-white/70' : 'text-white/70'">
                {{ viewCopy.sidebar.menuLabel }}
              </p>
              <p class="text-sm font-semibold truncate">{{ agencyName || 'Agencia' }}</p>
            </div>
            <button
              type="button"
              class="inline-flex h-8 w-8 items-center justify-center rounded-full border"
              :class="isDarkTheme ? 'border-white/40 text-white' : 'border-white/40 text-white'"
              @click="mobileMenuOpen = false"
            >
              <span class="sr-only">{{ viewCopy.sidebar.closeMenu }}</span>
              <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M6 6l12 12M6 18 18 6" />
              </svg>
            </button>
          </div>
          <nav class="space-y-2">
            <section
              v-for="section in sidebarSections"
              :key="`mobile-section-${section.id}`"
              class="pt-1 first:pt-0"
              :class="section.id !== sidebarSections[0]?.id ? 'mt-2' : ''"
            >
              <p class="px-2 pb-1 text-[10px] font-bold uppercase tracking-[0.12em] text-white/35">{{ section.label }}</p>
              <div class="space-y-1">
                <template v-for="item in section.items" :key="'mobile-' + item.id">
              <RouterLink
                v-if="item.type === 'link'"
                :to="item.to"
                class="flex items-center gap-2 rounded-lg px-3 py-2 text-[13px] font-medium transition"
                :class="[
                  'text-slate-100',
                  isTopLevelActive(item)
                    ? 'bg-[#2A5C38] border-l-[3px] border-l-[#3DCC5F]'
                    : 'hover:bg-white/8'
                ]"
                @click="mobileMenuOpen = false"
              >
                <span
                  :class="[
                    'flex h-7 w-7 items-center justify-center rounded-full',
                    'bg-white/10 text-slate-100'
                  ]"
                >
                  <svg
                    :viewBox="navIconViewBoxes[item.iconPath] || navIconViewBoxes.default"
                    :class="['h-4 w-4', navIconSizes[item.iconPath]]"
                    :stroke-width="navIconStrokeWidths[item.iconPath] || null"
                    v-html="navIcons[item.iconPath] || navIcons.default"
                  ></svg>
                </span>
                <span class="flex-1">{{ item.label }}</span>
                <span
                  v-if="getNavBadge(item.id) !== null"
                  class="rounded-full bg-[#3DCC5F] px-2 py-0.5 text-[10px] font-bold leading-none text-[#0F1F14]"
                >
                  {{ getNavBadge(item.id) }}
                </span>
              </RouterLink>
              <div v-else class="space-y-1">
                <button
                  type="button"
                  class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-[13px] font-medium transition text-slate-100"
                  :class="isParentActive(item) ? 'bg-[#2A5C38] border-l-[3px] border-l-[#3DCC5F]' : 'hover:bg-white/8'"
                  @click="toggleNavGroup(item.id)"
                >
                  <span
                    :class="[
                    'flex h-7 w-7 items-center justify-center rounded-full',
                      'bg-white/10 text-slate-100'
                    ]"
                  >
                    <svg
                      :viewBox="navIconViewBoxes[item.iconPath] || navIconViewBoxes.default"
                      :class="['h-4 w-4', navIconSizes[item.iconPath]]"
                      :stroke-width="navIconStrokeWidths[item.iconPath] || null"
                      v-html="navIcons[item.iconPath] || navIcons.default"
                    ></svg>
                  </span>
                  <span class="flex-1 text-left">{{ item.label }}</span>
                  <svg
                    viewBox="0 0 24 24"
                    class="mr-1 h-4 w-4 transition-transform"
                    :class="isGroupExpanded(item) ? 'rotate-180' : ''"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  >
                    <path d="m6 9 6 6 6-6" />
                  </svg>
                  <span
                    v-if="getNavBadge(item.id) !== null"
                    class="rounded-full bg-[#3DCC5F] px-2 py-0.5 text-[10px] font-bold leading-none text-[#0F1F14]"
                  >
                    {{ getNavBadge(item.id) }}
                  </span>
                </button>
                <div v-if="isGroupExpanded(item)" class="ml-9 space-y-1">
                  <RouterLink
                    v-for="child in item.children"
                    :key="'mobile-' + item.id + '-' + child.path"
                    :to="child.path"
                    class="flex items-center rounded-lg px-3 py-2 text-[12px] font-medium transition text-slate-100"
                    :class="isChildActive(child.path) ? 'bg-[#2A5C38] border-l-[3px] border-l-[#3DCC5F]' : 'hover:bg-white/8'"
                    @click="mobileMenuOpen = false"
                  >
                    <span>{{ child.label }}</span>
                  </RouterLink>
                </div>
              </div>
                </template>
              </div>
            </section>
          </nav>
          <div
            :class="[
              'mt-6 border-t pt-4 space-y-3',
              'border-slate-800'
            ]"
          >
            <button
              type="button"
              class="flex w-full items-center justify-between rounded-lg border px-3 py-2 text-sm font-semibold transition"
              :class="'border-white/15 bg-white/5 text-white hover:bg-white/10'"
              @click="toggleTheme"
            >
              <span>{{ viewCopy.themeToggle.label }}</span>
              <span
                :class="[
                  'relative inline-flex h-5 w-10 items-center rounded-full transition',
                  isDarkTheme ? 'bg-[#3DCC5F]' : 'bg-white/40'
                ]"
              >
                <span
                :class="[
                  'inline-block h-4 w-4 rounded-full bg-white shadow transition toggle-knob',
                  isDarkTheme ? 'translate-x-5' : 'translate-x-0'
                ]"
              ></span>
              </span>
            </button>
            <button
              type="button"
              @click="handleLogout"
              class="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition"
              :class="isDarkTheme ? 'text-white hover:bg-white/10' : 'text-white hover:bg-white/10'"
            >
              <span class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#3DCC5F] text-xs font-extrabold text-[#0F1F14]">
                {{ userInitial }}
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-[13px] font-semibold text-white">{{ userDisplayName }}</span>
                <span class="block text-[11px] text-white/50">{{ userRoleLabel }}</span>
              </span>
              <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-white/10 text-white/80">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M15 17l5-5-5-5" />
                  <path d="M20 12H9" />
                  <path d="M12 19H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h6" />
                </svg>
              </span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showWelcomeDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">{{ viewCopy.trial.welcome.eyebrow }}</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">
            {{ viewCopy.trial.welcome.titlePrefix }} {{ trialPlanName }} {{ viewCopy.trial.welcome.titleConnector }} {{ formattedDate }}
          </h2>
          <p class="mt-2 text-sm text-slate-600">
            {{ viewCopy.trial.welcome.description }}
          </p>
          <ul class="mt-4 list-disc space-y-1 pl-6 text-sm text-slate-600">
            <li v-for="(feature, featureIndex) in viewCopy.trial.welcome.features" :key="`trial-welcome-feature-${featureIndex}`">
              {{ feature }}
            </li>
          </ul>
          <p class="mt-4 text-sm text-slate-600">{{ viewCopy.trial.welcome.closing }}</p>
          <button
            class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            @click="startAgencySetupFlow"
          >
            {{ viewCopy.trial.welcome.cta }}
          </button>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showAgencySetupFlow"
        class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/80 px-4 py-6"
      >
        <div class="w-full max-w-2xl rounded-3xl bg-white p-8 shadow-2xl">
          <template v-if="agencySetupStep === 'name'">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">{{ viewCopy.onboarding.name.eyebrow }}</p>
                <h2 class="mt-3 text-3xl font-bold text-slate-900">{{ viewCopy.onboarding.name.title }}</h2>
                <p class="mt-2 text-base text-slate-500">{{ viewCopy.onboarding.name.description }}</p>
              </div>
              <div>
                <label class="text-sm font-semibold text-slate-600">{{ viewCopy.onboarding.name.label }}</label>
                <input
                  v-model="agencySetupForm.name"
                  class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-lg font-semibold text-slate-900"
                  :placeholder="viewCopy.onboarding.name.placeholder"
                />
              </div>
              <p v-if="agencySetupError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ agencySetupError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="requestAgencySetupClose">
                  {{ viewCopy.onboarding.actions.close }}
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
                  @click="goToNextAgencySetupStep"
                  :disabled="agencySetupStepLoading"
                >
                  {{ agencySetupStepLoading ? viewCopy.onboarding.actions.advancing : viewCopy.onboarding.actions.next }}
                </button>
              </div>
            </div>
          </template>
          <template v-else-if="agencySetupStep === 'logo'">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">{{ viewCopy.onboarding.logo.eyebrow }}</p>
                <h2 class="mt-3 text-3xl font-bold text-slate-900">{{ viewCopy.onboarding.logo.title }}</h2>
                <p class="mt-2 text-base text-slate-500">{{ viewCopy.onboarding.logo.description }}</p>
              </div>
              <ImageUploadField
                v-model="agencySetupForm.logo_url"
                :label="viewCopy.onboarding.logo.fieldLabel"
                :hint="viewCopy.onboarding.logo.hint"
                :enable-crop="true"
                :editor-title="viewCopy.onboarding.logo.editorTitle"
              />
              <p v-if="agencySetupError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ agencySetupError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="requestAgencySetupClose">
                  {{ viewCopy.onboarding.actions.close }}
                </button>
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="goToPreviousAgencySetupStep">
                  {{ viewCopy.onboarding.actions.back }}
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark"
                  @click="goToNextAgencySetupStep"
                >
                  {{ viewCopy.onboarding.actions.next }}
                </button>
              </div>
            </div>
          </template>
          <template v-else-if="agencySetupStep === 'color'">
            <div class="space-y-6">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.3em] text-emerald-500">{{ viewCopy.onboarding.color.eyebrow }}</p>
                <h2 class="mt-3 text-3xl font-bold text-slate-900">{{ viewCopy.onboarding.color.title }}</h2>
                <p class="mt-2 text-base text-slate-500">{{ viewCopy.onboarding.color.description }}</p>
              </div>
              <div class="flex flex-col gap-4 rounded-2xl border border-slate-100 p-4">
                <div class="flex items-center gap-4">
                  <div class="flex flex-col items-center">
                    <input
                      type="color"
                      v-model="agencySetupForm.primary_color"
                      class="h-16 w-16 cursor-pointer rounded-full border border-slate-200 bg-white p-2"
                    />
                    <span class="mt-2 text-xs font-semibold text-slate-500">{{ viewCopy.onboarding.color.pickerHint }}</span>
                  </div>
                  <div class="flex-1">
                    <label class="text-sm font-semibold text-slate-600">{{ viewCopy.onboarding.color.hexLabel }}</label>
                    <input
                      v-model="agencySetupForm.primary_color"
                      :placeholder="viewCopy.onboarding.color.placeholder"
                      class="mt-2 w-full rounded-2xl border border-slate-200 px-4 py-3 text-lg font-semibold uppercase tracking-wide text-slate-900"
                    />
                  </div>
                </div>
              </div>
              <p v-if="agencySetupError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ agencySetupError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-end gap-3">
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="requestAgencySetupClose">
                  {{ viewCopy.onboarding.actions.close }}
                </button>
                <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="goToPreviousAgencySetupStep">
                  {{ viewCopy.onboarding.actions.back }}
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
                  @click="submitAgencySetup"
                  :disabled="agencySetupSaving"
                >
                  {{ agencySetupSaving ? viewCopy.onboarding.actions.creating : viewCopy.onboarding.actions.createAgency }}
                </button>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="space-y-6 text-center">
              <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                <svg viewBox="0 0 24 24" class="h-8 w-8" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <h2 class="text-3xl font-bold text-slate-900">{{ viewCopy.onboarding.success.title }}</h2>
                <p class="mt-3 text-base text-slate-500">{{ viewCopy.onboarding.success.description }}</p>
              </div>
              <p v-if="createFirstPageError" class="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
                {{ createFirstPageError }}
              </p>
              <div class="mt-6 flex flex-wrap justify-center gap-3">
                <button class="rounded-full border border-slate-200 px-6 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50" @click="closeAgencySetupFlow">
                  {{ viewCopy.onboarding.actions.close }}
                </button>
                <button
                  class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-slate-300"
                  @click="createFirstPageFromOnboarding"
                  :disabled="createFirstPageLoading"
                >
                  {{ createFirstPageLoading ? viewCopy.onboarding.actions.creatingFirstPage : viewCopy.onboarding.actions.createFirstPage }}
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showAgencySetupUnsavedDialog"
        class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-md rounded-3xl bg-white p-6 text-center shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-500">{{ viewCopy.onboarding.unsaved.eyebrow }}</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">{{ viewCopy.onboarding.unsaved.title }}</h2>
          <p class="mt-2 text-sm text-slate-600">{{ viewCopy.onboarding.unsaved.description }}</p>
          <div class="mt-6 flex flex-wrap justify-center gap-3">
            <button class="rounded-full border border-slate-200 px-5 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50" @click="keepAgencySetupEditing">
              {{ viewCopy.onboarding.actions.continueEditing }}
            </button>
            <button class="rounded-full bg-brand px-6 py-2 text-sm font-semibold text-white shadow hover:bg-brand-dark" @click="confirmAgencySetupDiscard">
              {{ viewCopy.onboarding.actions.discardAndClose }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showTrialWarning3Days"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-amber-500">{{ viewCopy.trial.warn3.eyebrow }}</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">{{ viewCopy.trial.warn3.title }}</h2>
          <p class="mt-2 text-sm text-slate-600">
            {{ viewCopy.trial.warn3.description }}
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              @click="acknowledgeTrial('warn3')"
            >
              {{ viewCopy.trial.warn3.dismiss }}
            </button>
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="acknowledgeTrial('warn3', true)"
            >
              {{ viewCopy.trial.warn3.goPlans }}
            </button>
          </div>
        </div>
      </div>
    </transition>
    <transition name="fade">
      <div
        v-if="showTrialWarning1Day"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">{{ viewCopy.trial.warn1.eyebrow }}</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">{{ viewCopy.trial.warn1.title }}</h2>
          <p class="mt-2 text-sm text-slate-600">
            {{ viewCopy.trial.warn1.description }}
          </p>
          <div class="mt-6 flex flex-wrap justify-end gap-3">
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="acknowledgeTrial('warn1', true)"
            >
              {{ viewCopy.trial.warn1.subscribe }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showEndDialog"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 px-4"
      >
        <div class="w-full max-w-lg rounded-3xl bg-white p-8 shadow-2xl">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">{{ blockedAccessTitle.eyebrow }}</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">{{ blockedAccessTitle.title }}</h2>
          <p class="mt-2 text-sm text-slate-600">{{ blockedAccessDescription }}</p>
          <div class="mt-6 flex flex-wrap justify-end">
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="goToPlans"
            >
              {{ viewCopy.trial.blocked.goPlans }}
            </button>
          </div>
        </div>
      </div>
    </transition>


    <transition name="fade">
      <div
        v-if="showCookieConsent"
        class="fixed inset-x-6 bottom-4 z-50 md:left-1/2 md:top-auto md:bottom-8 md:-translate-x-1/2 md:w-3/4"
      >
        <div class="flex flex-col gap-2 rounded-3xl border border-slate-200 bg-white/95 p-4 shadow-2xl backdrop-blur">
          <div class="flex flex-col items-center gap-3 text-center md:flex-row md:items-center md:justify-center md:text-left">
            <div class="md:flex-1">
              <p class="text-xs font-semibold uppercase tracking-[0.3em] text-slate-500">{{ viewCopy.cookies.title }}</p>
              <p class="text-sm text-slate-600">
                <span class="block">{{ viewCopy.cookies.descriptionLine1 }}</span>
                <span class="block">{{ viewCopy.cookies.descriptionLine2 }}</span>
              </p>
            </div>
            <div class="flex w-full flex-wrap items-center justify-center gap-2 md:w-auto md:justify-center">
              <button
                type="button"
                class="order-1 text-[11px] font-semibold text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline md:order-none"
                @click="dismissCookies"
              >
                {{ viewCopy.cookies.skip }}
              </button>
              <button
                type="button"
                class="order-2 w-full rounded-full bg-slate-900 px-5 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 md:order-none md:w-auto md:text-sm"
                @click="acceptCookies"
              >
                {{ viewCopy.cookies.accept }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <a
      href="https://wa.me/5553991754616"
      target="_blank"
      rel="noopener"
      class="group fixed bottom-5 right-5 z-40 inline-flex h-14 min-w-[3.5rem] items-center justify-center rounded-full bg-[#25D366] px-4 text-white shadow-2xl overflow-hidden transition-all duration-200 hover:brightness-110 group-hover:justify-start"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path
          d="M19.05 4.91A9.82 9.82 0 0 0 12.04 2c-5.46 0-9.91 4.45-9.91 9.91c0 1.75.46 3.45 1.32 4.95L2.05 22l5.25-1.38c1.45.79 3.08 1.21 4.74 1.21c5.46 0 9.91-4.45 9.91-9.91c0-2.65-1.03-5.14-2.9-7.01m-7.01 15.24c-1.48 0-2.93-.4-4.2-1.15l-.3-.18l-3.12.82l.83-3.04l-.2-.31a8.26 8.26 0 0 1-1.26-4.38c0-4.54 3.7-8.24 8.24-8.24c2.2 0 4.27.86 5.82 2.42a8.18 8.18 0 0 1 2.41 5.83c.02 4.54-3.68 8.23-8.22 8.23m4.52-6.16c-.25-.12-1.47-.72-1.69-.81c-.23-.08-.39-.12-.56.12c-.17.25-.64.81-.78.97c-.14.17-.29.19-.54.06c-.25-.12-1.05-.39-1.99-1.23c-.74-.66-1.23-1.47-1.38-1.72c-.14-.25-.02-.38.11-.51c.11-.11.25-.29.37-.43s.17-.25.25-.41c.08-.17.04-.31-.02-.43s-.56-1.34-.76-1.84c-.2-.48-.41-.42-.56-.43h-.48c-.17 0-.43.06-.66.31c-.22.25-.86.85-.86 2.07s.89 2.4 1.01 2.56c.12.17 1.75 2.67 4.23 3.74c.59.26 1.05.41 1.41.52c.59.19 1.13.16 1.56.1c.48-.07 1.47-.6 1.67-1.18c.21-.58.21-1.07.14-1.18s-.22-.16-.47-.28"
        />
      </svg>
      <span class="ml-0 max-w-0 overflow-hidden whitespace-nowrap text-sm font-semibold opacity-0 transition-all duration-200 group-hover:ml-3 group-hover:max-w-[140px] group-hover:opacity-100">{{ viewCopy.support.prompt }}</span>
    </a>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import SidebarLogo from "../assets/Logo Branco - Roteiro Online.png";
import ImageUploadField from "../components/admin/inputs/ImageUploadField.vue";
import api from "../services/api";
import { useAgencyStore } from "../store/useAgencyStore";
import { useAuthStore } from "../store/useAuthStore";
import { useLeadCaptureStore } from "../store/useLeadCaptureStore";
import { useThemeStore } from "../store/useThemeStore";
import { getPlanLabel } from "../utils/planLabels";
import { addTagsToContactByEmail, syncPlanTagForEmail, viajeChatTagIds } from "../services/viajeChat";
import { slugify } from "../utils/slugify";
import { createAdminLocalizer } from "../utils/adminI18n";

const route = useRoute();
const router = useRouter();
const agencyStore = useAgencyStore();
const auth = useAuthStore();
const leadStore = useLeadCaptureStore();
const routeRequiresAuth = computed(() => route.matched.some(record => record.meta?.requiresAuth));
const showAuthSplash = computed(() => {
  if (!routeRequiresAuth.value) return false;
  if (!auth.token) return false;
  return auth.isHydrating || !auth.user;
});
const navPageCount = ref<number | null>(null);
const navLeadCount = ref<number | null>(null);
const userDisplayName = computed(() => {
  const user = auth.user as Record<string, unknown> | null;
  if (!user) return "Usuário";
  const name = (user.name as string) || (user.full_name as string) || (user.username as string);
  if (name && name.trim()) return name.trim().split(/\s+/)[0];
  const email = user.email as string | undefined;
  return email?.trim().split("@")[0] || "Usuário";
});
const userInitial = computed(() => {
  const name = userDisplayName.value.trim();
  return name ? name.charAt(0).toUpperCase() : "U";
});
const userRoleLabel = computed(() => (auth.user?.is_superuser ? "Admin" : "Usuário"));
const themeStore = useThemeStore();
const COOKIE_KEY = "global_cookie_consent";
const t = createAdminLocalizer();

const navCopy = {
  dashboard: { pt: "Dashboard", es: "Dashboard" },
  adminMaster: { pt: "Admin Master", es: "Admin Master" },
  pages: { pt: "Páginas", es: "Páginas" },
  leads: { pt: "Leads", es: "Leads" },
  clients: { pt: "Clientes", es: "Clientes" },
  integrations: { pt: "Integrações", es: "Integraciones" },
  domains: { pt: "Domínios", es: "Dominios" },
  agency: { pt: "Minha Agência", es: "Mi Agencia" },
  profile: { pt: "Perfil", es: "Perfil" },
  lessons: { pt: "Aulas", es: "Cursos" },
  plans: { pt: "Planos", es: "Planes" }
} as const;

const navLabel = (key: keyof typeof navCopy) => t(navCopy[key]);
const viewCopy = {
  themeToggle: {
    title: t({ pt: "Tema escuro", es: "Tema oscuro" }),
    active: t({ pt: "Ativo", es: "Activo" }),
    inactive: t({ pt: "Desativado", es: "Desactivado" }),
    label: t({ pt: "Tema escuro", es: "Tema oscuro" })
  },
  sidebar: {
    logout: t({ pt: "Sair", es: "Salir" }),
    menuLabel: t({ pt: "Menu", es: "Menú" }),
    openMenu: t({ pt: "Abrir menu", es: "Abrir menú" }),
    closeMenu: t({ pt: "Fechar", es: "Cerrar" })
  },
  support: {
    prompt: t({ pt: "Precisa de ajuda?", es: "¿Necesita ayuda?" })
  },
  trial: {
    welcome: {
      eyebrow: t({ pt: "Bem-vindo ao trial profissional", es: "Bienvenido al trial profesional" }),
      titlePrefix: t({ pt: "Plano", es: "Plan" }),
      titleConnector: t({ pt: "liberado até", es: "habilitado hasta" }),
      description: t({
        pt: "Durante estes 7 dias você pode testar tudo que usamos nos planos pagos:",
        es: "Durante estos 7 días puedes probar todo lo que usamos en los planes pagos:"
      }),
      features: [
        t({ pt: "Criar até 3 páginas completas, com seções ilimitadas.", es: "Crear hasta 3 páginas completas con secciones ilimitadas." }),
        t({
          pt: "Duplicar roteiros, personalizar blocos premium e usar pixels ilimitados.",
          es: "Duplicar itinerarios, personalizar bloques premium y usar píxeles ilimitados."
        }),
        t({
          pt: "Publicar páginas sem rodapé da versão gratuita e acompanhar métricas em tempo real.",
          es: "Publicar páginas sin el pie de la versión gratuita y seguir métricas en tiempo real."
        })
      ],
      closing: t({
        pt: "Explore à vontade e chame nosso time se quiser montar um roteiro profissional.",
        es: "Explora con libertad y pídenos ayuda si quieres armar un itinerario profesional."
      }),
      cta: t({ pt: "Começar agora", es: "Comenzar ahora" })
    },
    warn3: {
      eyebrow: t({ pt: "Faltam 3 dias", es: "Faltan 3 días" }),
      title: t({ pt: "Seu período trial termina em breve", es: "Tu período de prueba termina pronto" }),
      description: t({
        pt: "Em 3 dias o acesso ao editor será bloqueado. Escolha um plano para continuar criando roteiros ilimitados.",
        es: "En 3 días se bloqueará el acceso al editor. Elige un plan para seguir creando itinerarios ilimitados."
      }),
      dismiss: t({ pt: "Depois", es: "Después" }),
      goPlans: t({ pt: "Ver planos", es: "Ver planes" })
    },
    warn1: {
      eyebrow: t({ pt: "Últimas horas", es: "Últimas horas" }),
      title: t({ pt: "Seu trial termina amanhã", es: "Tu trial termina mañana" }),
      description: t({
        pt: "Contrate agora para manter suas páginas ativas e seguir publicando novos roteiros sem interrupção.",
        es: "Contrata ahora para mantener tus páginas activas y seguir publicando nuevos itinerarios sin interrupción."
      }),
      subscribe: t({ pt: "Assinar agora", es: "Suscribirme ahora" })
    },
    blocked: {
      eyebrow: t({ pt: "Trial encerrado", es: "Trial finalizado" }),
      title: t({ pt: "Você atingiu o limite do plano trial", es: "Alcanzaste el límite del plan trial" }),
      description: t({
        pt: "Assine um plano para desbloquear seu painel e republicar seus roteiros.",
        es: "Suscríbete para desbloquear tu panel y volver a publicar tus itinerarios."
      }),
      goPlans: t({ pt: "Ir para os planos", es: "Ir a los planes" }),
      close: t({ pt: "Fechar", es: "Cerrar" })
    }
  },
  subscription: {
    blocked: {
      eyebrow: t({ pt: "Plano expirado", es: "Plan expirado" }),
      title: t({ pt: "Renove para voltar a editar", es: "Renueva para volver a editar" }),
      description: t({
        pt: "Seu período contratado terminou. Para voltar a editar e publicar roteiros, renove seu plano.",
        es: "Tu período contratado terminó. Para volver a editar y publicar itinerarios, renueva tu plan."
      })
    }
  },
  cookies: {
    title: t({ pt: "Cookies", es: "Cookies" }),
    descriptionLine1: t({
      pt: "Utilizamos cookies e armazenamento local para manter sua sessão segura e salvar preferências.",
      es: "Usamos cookies y almacenamiento local para mantener tu sesión segura y guardar preferencias."
    }),
    descriptionLine2: t({
      pt: "Se optar por continuar sem aceitar, alguns recursos podem apresentar limitações.",
      es: "Si decides seguir sin aceptar, algunas funciones pueden presentar limitaciones."
    }),
    skip: t({ pt: "Continuar sem aceitar", es: "Seguir sin aceptar" }),
    accept: t({ pt: "Aceitar cookies", es: "Aceptar cookies" })
  },
  onboarding: {
    firstPageTitle: t({ pt: "Meu primeiro roteiro", es: "Mi primer itinerario" }),
    name: {
      eyebrow: t({ pt: "Comece por aqui", es: "Empieza por aquí" }),
      title: t({ pt: "Qual nome da sua agência?", es: "¿Cuál es el nombre de tu agencia?" }),
      description: t({ pt: "Esse nome aparece no painel e nas páginas. Você pode alterar depois.", es: "Este nombre aparece en el panel y en las páginas. Puedes cambiarlo después." }),
      label: t({ pt: "Nome da agência", es: "Nombre de la agencia" }),
      placeholder: t({ pt: "Ex.: MariaTur", es: "Ej.: MariaTur" })
    },
    logo: {
      eyebrow: t({ pt: "Personalize", es: "Personaliza" }),
      title: t({ pt: "Logo da sua agência", es: "Logo de tu agencia" }),
      description: t({ pt: "Envie o arquivo da sua marca. Você pode trocar depois.", es: "Sube el archivo de tu marca. Puedes cambiarlo despues." }),
      fieldLabel: t({ pt: "Logo", es: "Logo" }),
      hint: t({ pt: "Formatos permitidos: JPG e PNG - Tamanho máximo: 10MB", es: "Formatos permitidos: JPG y PNG - Tamanho máximo: 10MB" }),
      editorTitle: t({ pt: "Ajuste a logo da agência", es: "Ajusta el logo de la agencia" })
    },
    color: {
      eyebrow: t({ pt: "Defina o estilo", es: "Define el estilo" }),
      title: t({ pt: "Qual a cor principal da sua agência?", es: "¿Cuál es el color principal de tu agencia?" }),
      description: t({ pt: "Usamos essa cor nos botões e destaques padrão do editor.", es: "Usamos este color en los botones y destacados predeterminados del editor." }),
      pickerHint: t({ pt: "Clique aqui para alterar", es: "Haz clic aquí para cambiar" }),
      hexLabel: t({ pt: "Código hexadecimal", es: "Código hexadecimal" }),
      placeholder: t({ pt: "#41ce5f", es: "#41ce5f" })
    },
    success: {
      title: t({ pt: "Parabéns, sua agência foi criada!", es: "¡Felicidades, tu agencia fue creada!" }),
      description: t({ pt: "Agora você pode criar sua primeira página personalizada.", es: "Ahora puedes crear tu primera página personalizada." })
    },
    unsaved: {
      eyebrow: t({ pt: "Atenção", es: "Atencion" }),
      title: t({ pt: "Há alterações não salvas", es: "Hay cambios no guardados" }),
      description: t({ pt: "Se fechar agora, você perderá o que preencheu. Deseja realmente sair?", es: "Si cierras ahora, perderás lo que completaste. ¿Deseas salir?" })
    },
    actions: {
      close: t({ pt: "Fechar", es: "Cerrar" }),
      next: t({ pt: "Avançar", es: "Avanzar" }),
      advancing: t({ pt: "Avançando...", es: "Avanzando..." }),
      back: t({ pt: "Voltar", es: "Volver" }),
      creating: t({ pt: "Criando...", es: "Creando..." }),
      createAgency: t({ pt: "Criar agência", es: "Crear agencia" }),
      creatingFirstPage: t({ pt: "Criando...", es: "Creando..." }),
      createFirstPage: t({ pt: "Criar minha primeira página", es: "Crear mi primera página" }),
      continueEditing: t({ pt: "Continuar editando", es: "Seguir editando" }),
      discardAndClose: t({ pt: "Descartar e fechar", es: "Descartar y cerrar" })
    },
    errors: {
      missingName: t({ pt: "Informe o nome da sua agência.", es: "Informa el nombre de tu agencia." }),
      cannotAdvance: t({ pt: "Não foi possível avançar. Tente novamente.", es: "No fue posible avanzar. Intenta nuevamente." }),
      cannotCreateAgency: t({ pt: "Não foi possível criar a agência. Tente novamente.", es: "No fue posible crear la agencia. Intenta nuevamente." }),
      mustCreateAgency: t({ pt: "Crie sua agência antes de adicionar páginas.", es: "Crea tu agencia antes de agregar páginas." }),
      cannotCreatePage: t({ pt: "Não foi possível criar a página agora.", es: "No fue posible crear la página ahora." }),
      slugUnavailable: t({ pt: "Não foi possível gerar um slug disponível para esta agência. Ajuste o nome e tente novamente.", es: "No fue posible generar un slug disponible para esta agencia. Ajusta el nombre e inténtalo nuevamente." })
    }
  }
} as const;

const isDarkTheme = computed(() => themeStore.isDark);
const themeWrapperClass = computed(() => (isDarkTheme.value ? "dark-theme" : "light-theme"));
const toggleTheme = () => themeStore.toggleTheme();

const showCookieConsent = ref(false);
const hasWindow = typeof window !== "undefined";
const bodyDarkClass = "admin-body-dark";
const bodyLightClass = "admin-body-light";
const isMobileViewport = ref(false);
let removeViewportWatcher: (() => void) | null = null;

const syncBodyTheme = (dark: boolean) => {
  if (!hasWindow) return;
  document.body.classList.toggle(bodyDarkClass, dark);
  document.body.classList.toggle(bodyLightClass, !dark);
};

watch(
  isDarkTheme,
  value => {
    syncBodyTheme(value);
  },
  { immediate: true }
);

const syncViewport = () => {
  if (!hasWindow) return;
  isMobileViewport.value = window.innerWidth < 768;
};

const setupViewportWatcher = () => {
  if (!hasWindow) return;
  syncViewport();
  const handler = () => syncViewport();
  window.addEventListener("resize", handler);
  removeViewportWatcher = () => {
    window.removeEventListener("resize", handler);
    removeViewportWatcher = null;
  };
};

const navIcons: Record<string, string> = {
  default: '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 2a8 8 0 1 1-8 8 8 8 0 0 1 8-8zm0 3v6l4 2" />',
  "/admin/dashboard": '<path fill="none" stroke="currentColor" stroke-width="1.8" d="M4 5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zm10 0a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1zM4 16a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1zm10-3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1z"/>' ,
  "/admin/pages": '<g fill="none" stroke="currentColor" stroke-width="2"><path d="M6.142 6.142C8.904 3.381 10.284 2 12 2s3.096 1.38 5.858 4.142S22 10.284 22 12s-1.38 3.096-4.142 5.858S13.716 22 12 22s-3.096-1.38-5.858-4.142S2 13.716 2 12s1.38-3.096 4.142-5.858Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M16 11.5L13.333 9M16 11.5L13.333 14M16 11.5h-5.333C9.777 11.5 8 12 8 14"/></g>',
  "/admin/leads": '<path fill="currentColor" d="m17 21l1.8 1.77c.5.5 1.2.1 1.2-.49V18l2.8-3.4A1 1 0 0 0 22 13h-7c-.8 0-1.3 1-.8 1.6L17 18zm-2-1H2v-3c0-2.7 5.3-4 8-4c.6 0 1.3.1 2.1.2c-.2.6-.1 1.3.1 1.9c-.7-.1-1.5-.2-2.2-.2c-3 0-6.1 1.5-6.1 2.1v1.1h10.6l.5.6zM10 4C7.8 4 6 5.8 6 8s1.8 4 4 4s4-1.8 4-4s-1.8-4-4-4m0 6c-1.1 0-2-.9-2-2s.9-2 2-2s2 .9 2 2s-.9 2-2 2"/>',
  "/admin/clientes": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="9" cy="8" r="3"/><path d="M3 19c0-3 2.5-5 6-5s6 2 6 5"/><path d="M18 8h3M19.5 6.5v3"/></g>',
  "/admin/integracoes": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><path d="M18.364 19.364a9 9 0 1 0-12.728 0"/><path d="M15.536 16.536a5 5 0 1 0-7.072 0"/><path d="M11 13a1 1 0 1 0 2 0a1 1 0 1 0-2 0"/></g>',
  "/admin/agency": '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.3" d="M4 11.452V16.8c0 1.12 0 1.68.218 2.109c.192.376.497.682.874.873c.427.218.987.218 2.105.218h9.606c1.118 0 1.677 0 2.104-.218a2 2 0 0 0 .875-.873c.218-.428.218-.987.218-2.105v-5.352c0-.534 0-.801-.065-1.05a2 2 0 0 0-.28-.617c-.145-.213-.345-.39-.748-.741l-4.8-4.2c-.746-.653-1.12-.98-1.54-1.104c-.37-.11-.764-.11-1.135 0c-.42.124-.792.45-1.538 1.102L5.093 9.044c-.402.352-.603.528-.747.74a2 2 0 0 0-.281.618C4 10.65 4 10.918 4 11.452"/>',
  "/admin/domains": '<g transform="translate(3 3) scale(1.1)"><path fill="currentColor" d="M9 0a9 9 0 1 0 0 18A9 9 0 0 0 9 0M1.11 9.68h2.51c.04.91.167 1.814.38 2.7H1.84a7.9 7.9 0 0 1-.73-2.7m8.57-5.4V1.19a4.13 4.13 0 0 1 2.22 2q.308.521.54 1.08zm3.22 1.35c.232.883.37 1.788.41 2.7H9.68v-2.7zM8.32 1.19v3.09H5.56A8.5 8.5 0 0 1 6.1 3.2a4.13 4.13 0 0 1 2.22-2.01m0 4.44v2.7H4.7c.04-.912.178-1.817.41-2.7zm-4.7 2.69H1.11a7.9 7.9 0 0 1 .73-2.7H4a14 14 0 0 0-.38 2.7M4.7 9.68h3.62v2.7H5.11a13 13 0 0 1-.41-2.7m3.63 4v3.09a4.13 4.13 0 0 1-2.22-2a8.5 8.5 0 0 1-.54-1.08zm1.35 3.09v-3.04h2.76a8.5 8.5 0 0 1-.54 1.08a4.13 4.13 0 0 1-2.22 2zm0-4.44v-2.7h3.62a13 13 0 0 1-.41 2.7zm4.71-2.7h2.51a7.9 7.9 0 0 1-.73 2.7H14c.21-.87.337-1.757.38-2.65zm0-1.35A14 14 0 0 0 14 5.63h2.16c.403.85.65 1.764.73 2.7zm1-4H13.6a8.9 8.9 0 0 0-1.39-2.52a8 8 0 0 1 3.14 2.52zm-9.6-2.52A8.9 8.9 0 0 0 4.4 4.28H2.65a8 8 0 0 1 3.14-2.52m-3.15 12H4.4a8.9 8.9 0 0 0 1.39 2.52a8 8 0 0 1-3.14-2.55zm9.56 2.52a8.9 8.9 0 0 0 1.39-2.52h1.76a8 8 0 0 1-3.14 2.48z"/></g>',
  "/admin/perfil": '<g fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 0 0-16 0"/></g>',
  "/admin/planos": '<path fill="currentColor" d="m21.41 11.58-9-9C12.05 2.22 11.55 2 11 2H4c-1.1 0-2 .9-2 2v7c0 .55.22 1.05.59 1.42l9 9c.36.36.86.58 1.41.58s1.05-.22 1.41-.59l7-7c.37-.36.59-.86.59-1.41s-.23-1.06-.59-1.42M13 20.01L4 11V4h7v-.01l9 9z"/><circle cx="6.5" cy="6.5" r="1.5" fill="currentColor"/>',
  "/admin/administracao": '<path fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m12 17.75l-6.172 3.245l1.179-6.873l-5-4.867l6.9-1l3.086-6.253l3.086 6.253l6.9 1l-5 4.867l1.179 6.873z"/>',
  "/admin/aulas": '<path fill="currentColor" d="m164.44 105.34-48-32A8 8 0 0 0 104 80v64a8 8 0 0 0 12.44 6.66l48-32a8 8 0 0 0 0-13.32M120 129.05V95l25.58 17ZM216 40H40a16 16 0 0 0-16 16v112a16 16 0 0 0 16 16h176a16 16 0 0 0 16-16V56a16 16 0 0 0-16-16m0 128H40V56h176zm16 40a8 8 0 0 1-8 8H32a8 8 0 0 1 0-16h192a8 8 0 0 1 8 8"/>' ,

};

const navIconSizes: Record<string, string> = {
  "/admin/agency": "h-4 w-4"
};

const navIconViewBoxes: Record<string, string> = {
  default: "0 0 24 24",
  "/admin/aulas": "0 0 256 256"
};

const navIconStrokeWidths: Record<string, string> = {};

type AdminNavChild = {
  label: string;
  path: string;
};

type AdminNavLinkItem = {
  id: string;
  type: "link";
  label: string;
  to: string;
  iconPath: string;
};

type AdminNavGroupItem = {
  id: string;
  type: "group";
  label: string;
  basePath: string;
  iconPath: string;
  children: AdminNavChild[];
};

type AdminNavItem = AdminNavLinkItem | AdminNavGroupItem;
type SidebarSection = { id: string; label: string; itemIds: string[]; items: AdminNavItem[] };

const routeTitleMap: Record<string, string> = {
  dashboard: navLabel("dashboard"),
  pages: navLabel("pages"),
  leads: navLabel("leads"),
  "leads-forms": t({ pt: "Formulários", es: "Formularios" }),
  "leads-opportunities": t({ pt: "Oportunidades", es: "Oportunidades" }),
  "leads-clients": navLabel("clients"),
  "leads-settings": t({ pt: "Configurações", es: "Configuraciones" }),
  "client-detail": navLabel("clients"),
  "admin-management-dashboard": navLabel("dashboard"),
  "admin-management-monitor": t({ pt: "Monitor", es: "Monitor" }),
  "admin-management-users": t({ pt: "Usuários", es: "Usuarios" }),
  "admin-management-lessons": t({ pt: "Gestão de aulas", es: "Gestión de cursos" }),
  "admin-management-templates": t({ pt: "Templates", es: "Templates" }),
  "admin-management-flight-apis": t({ pt: "APIs de voo", es: "APIs de vuelo" }),
  "admin-management-banners": t({ pt: "Banners", es: "Banners" }),
  "page-edit": t({ pt: "Editar página", es: "Editar página" }),
  lessons: navLabel("lessons"),
  "agency-settings": navLabel("agency"),
  "agency-domains": navLabel("domains"),
  plans: navLabel("plans"),
  integrations: navLabel("integrations"),
  profile: navLabel("profile"),
  "admin-management": navLabel("adminMaster")
};
const canAccessCustomDomains = computed(() => true);

const navGroupExpandedState = ref<Record<string, boolean>>({});

const adminNavigation = computed<AdminNavItem[]>(() => {
  const items: AdminNavItem[] = [
    { id: "dashboard", type: "link", label: navLabel("dashboard"), to: "/admin/dashboard", iconPath: "/admin/dashboard" },
    { id: "pages", type: "link", label: navLabel("pages"), to: "/admin/pages", iconPath: "/admin/pages" },
    {
      id: "leads",
      type: "group",
      label: t({ pt: "Captação de leads", es: "Captacion" }),
      basePath: "/admin/leads",
      iconPath: "/admin/leads",
      children: [
        { label: t({ pt: "Formulários", es: "Formularios" }), path: "/admin/leads/forms" },
        { label: t({ pt: "Oportunidades", es: "Oportunidades" }), path: "/admin/leads/opportunities" },
        { label: navLabel("clients"), path: "/admin/leads/clients" },
        { label: t({ pt: "Configurações", es: "Configuraciones" }), path: "/admin/leads/settings" }
      ]
    },
    { id: "integrations", type: "link", label: navLabel("integrations"), to: "/admin/integracoes", iconPath: "/admin/integracoes" },
    { id: "agency", type: "link", label: navLabel("agency"), to: "/admin/agency", iconPath: "/admin/agency" },
    { id: "profile", type: "link", label: navLabel("profile"), to: "/admin/perfil", iconPath: "/admin/perfil" },
    { id: "lessons", type: "link", label: navLabel("lessons"), to: "/admin/aulas", iconPath: "/admin/aulas" }
  ];
  if (canAccessCustomDomains.value) {
    items.splice(5, 0, { id: "domains", type: "link", label: navLabel("domains"), to: "/admin/domains", iconPath: "/admin/domains" });
  }
  if (auth.user?.is_superuser) {
    items.splice(1, 0, {
      id: "admin-master",
      type: "group",
      label: navLabel("adminMaster"),
      basePath: "/admin/administracao",
      iconPath: "/admin/administracao",
      children: [
        { label: t({ pt: "Dashboard", es: "Dashboard" }), path: "/admin/administracao/dashboard" },
        { label: t({ pt: "Monitor", es: "Monitor" }), path: "/admin/administracao/monitor" },
        { label: t({ pt: "Usuários", es: "Usuarios" }), path: "/admin/administracao/usuarios" },
        { label: t({ pt: "Gestão de aulas", es: "Gestión de cursos" }), path: "/admin/administracao/aulas" },
        { label: t({ pt: "Templates", es: "Templates" }), path: "/admin/administracao/templates" },
        { label: t({ pt: "APIs de voo", es: "APIs de vuelo" }), path: "/admin/administracao/apis-voo" },
        { label: t({ pt: "Banners", es: "Banners" }), path: "/admin/administracao/banners" }
      ]
    });
  }
  return items;
});

const sidebarSections = computed<SidebarSection[]>(() => {
  const items = adminNavigation.value;
  const byId = new Map(items.map(item => [item.id, item]));
  const sectionsBase: Array<Omit<SidebarSection, "items">> = [
    {
      id: "principal",
      label: t({ pt: "Principal", es: "Principal" }),
      itemIds: ["dashboard", "admin-master", "pages", "leads"]
    },
    {
      id: "configurar",
      label: t({ pt: "Configurar", es: "Configurar" }),
      itemIds: ["integrations", "agency", "domains", "profile"]
    },
    {
      id: "aprender",
      label: t({ pt: "Aprender", es: "Aprender" }),
      itemIds: ["lessons"]
    }
  ];

  return sectionsBase
    .map(section => ({
      ...section,
      items: section.itemIds
        .map(id => byId.get(id))
        .filter((item): item is AdminNavItem => Boolean(item))
    }))
    .filter(section => section.items.length > 0);
});

const isPathActive = (path: string) => route.path === path || route.path.startsWith(`${path}/`);

const isChildActive = (path: string) => isPathActive(path);

const isTopLevelActive = (item: AdminNavLinkItem) => isPathActive(item.to);

const isParentActive = (item: AdminNavGroupItem) => isPathActive(item.basePath);

const isGroupExpanded = (item: AdminNavGroupItem) => isParentActive(item) || Boolean(navGroupExpandedState.value[item.id]);

const toggleNavGroup = (groupId: string) => {
  navGroupExpandedState.value[groupId] = !navGroupExpandedState.value[groupId];
};

const getNavBadge = (itemId: string): string | null => {
  if (itemId === "pages" && navPageCount.value !== null) {
    return navPageCount.value > 99 ? "99+" : String(navPageCount.value);
  }
  if (itemId === "leads" && navLeadCount.value !== null) {
    return navLeadCount.value > 99 ? "99+" : String(navLeadCount.value);
  }
  return null;
};

const loadNavCounters = async () => {
  const agencyId = agencyStore.currentAgencyId;
  if (!agencyId) {
    navPageCount.value = null;
    navLeadCount.value = null;
    return;
  }

  const [pagesResult, leadsResult] = await Promise.allSettled([
    api.get<Array<unknown>>("/pages", { params: { agency_id: agencyId } }),
    leadStore.fetchContacts(undefined, true)
  ]);

  if (pagesResult.status === "fulfilled") {
    navPageCount.value = Array.isArray(pagesResult.value.data) ? pagesResult.value.data.length : 0;
  }
  if (leadsResult.status === "fulfilled") {
    navLeadCount.value = leadStore.totalContacts ?? 0;
  }
};

watch(
  () => [agencyStore.currentAgencyId, auth.user?.id] as const,
  () => {
    void loadNavCounters();
  },
  { immediate: true }
);

const currentPageTitle = computed(() => {
  const routeName = typeof route.name === "string" ? route.name : null;
  if (routeName && routeTitleMap[routeName]) {
    return routeTitleMap[routeName];
  }
  for (const item of adminNavigation.value) {
    if (item.type === "link" && isTopLevelActive(item)) {
      return item.label;
    }
    if (item.type === "group") {
      const matchedChild = item.children.find(child => isChildActive(child.path));
      if (matchedChild) return matchedChild.label;
      if (isParentActive(item)) return item.label;
    }
  }
  return navLabel("dashboard");
});

const pageTitleRowPaddingClass = computed(() => {
  const path = route.path;
  if (path.startsWith("/admin/administracao")) return "px-4 md:px-8";
  if (path.startsWith("/admin/dashboard")) return "px-4 md:px-8";
  if (path.startsWith("/admin/leads")) return "px-4 md:px-5";
  if (path.startsWith("/admin/pages")) return "px-4 md:px-5";
  return "px-4 md:px-6";
});

const activeClass = computed(() => "bg-[#2A5C38] text-white border-l-[3px] border-l-[#3DCC5F]");
const inactiveClass = computed(() => "text-slate-200 hover:bg-white/8 hover:text-white");
const childActiveClass = computed(() => "bg-[#2A5C38] text-white border-l-[3px] border-l-[#3DCC5F]");
const childInactiveClass = computed(() => "text-slate-300 hover:bg-white/8 hover:text-white");

const agencyName = computed(() => agencyStore.currentAgency?.name || agencyStore.agencies[0]?.name || "");
const sidebarLogoSrc = SidebarLogo;

const checkCookieConsent = () => {
  if (typeof window === "undefined") return;
  const consent = localStorage.getItem(COOKIE_KEY);
  showCookieConsent.value = !consent;
};

const acceptCookies = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_KEY, "accepted");
  }
  showCookieConsent.value = false;
};

const dismissCookies = () => {
  if (typeof window !== "undefined") {
    localStorage.setItem(COOKIE_KEY, "dismissed");
  }
  showCookieConsent.value = false;
};

const handleLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};

const showWelcomeDialog = ref(false);
const showEndDialog = ref(false);
const showTrialWarning3Days = ref(false);
const showTrialWarning1Day = ref(false);
const mobileMenuOpen = ref(false);
const trialPlanName = computed(() => getPlanLabel(auth.user?.trial_plan));
const planTagMap: Record<string, string> = {
  essencial: viajeChatTagIds.PLANO_PROFISSIONAL,
  growth: viajeChatTagIds.PLANO_AGENCIA,
  infinity: viajeChatTagIds.PLANO_ESCALA
};
const planTagIds = Object.values(planTagMap);
const lastSyncedPlan = ref<string | null>(null);
let planTagSyncQueue = Promise.resolve();

type AgencySetupStep = "name" | "logo" | "color" | "success";
interface AgencySetupFormState {
  name: string;
  logo_url: string | null;
  primary_color: string;
}

const DEFAULT_AGENCY_COLOR = "#41ce5f";
const createEmptyAgencySetup = (): AgencySetupFormState => ({
  name: "",
  logo_url: null,
  primary_color: DEFAULT_AGENCY_COLOR
});

const agencySetupForm = reactive<AgencySetupFormState>(createEmptyAgencySetup());
const agencySetupStep = ref<AgencySetupStep>("name");
const showAgencySetupFlow = ref(false);
const agencySetupCreatedId = ref<number | null>(null);
const agencySetupSaving = ref(false);
const agencySetupStepLoading = ref(false);
const agencySetupError = ref("");
const createFirstPageLoading = ref(false);
const createFirstPageError = ref("");
const showAgencySetupUnsavedDialog = ref(false);

const serializeAgencySetup = () => ({
  name: agencySetupForm.name || "",
  logo_url: agencySetupForm.logo_url || null,
  primary_color: agencySetupForm.primary_color || DEFAULT_AGENCY_COLOR
});

const agencySetupSnapshot = ref(JSON.stringify(serializeAgencySetup()));
const agencySetupDirty = computed(
  () => showAgencySetupFlow.value && JSON.stringify(serializeAgencySetup()) !== agencySetupSnapshot.value
);

const markAgencySetupSnapshot = () => {
  agencySetupSnapshot.value = JSON.stringify(serializeAgencySetup());
};

const resetAgencySetupForm = () => {
  agencySetupForm.name = "";
  agencySetupForm.logo_url = null;
  agencySetupForm.primary_color = DEFAULT_AGENCY_COLOR;
  agencySetupStep.value = "name";
  agencySetupError.value = "";
  createFirstPageError.value = "";
  createFirstPageLoading.value = false;
  agencySetupCreatedId.value = null;
  agencySetupStepLoading.value = false;
  markAgencySetupSnapshot();
};

markAgencySetupSnapshot();

const trialStartDate = computed(() => (auth.user?.trial_started_at ? new Date(auth.user.trial_started_at) : null));
const trialEndDate = computed(() => (auth.user?.trial_ends_at ? new Date(auth.user.trial_ends_at) : null));
const trialActive = computed(() => {
  if (!auth.user?.trial_plan) return false;
  if (!trialStartDate.value || !trialEndDate.value) return false;
  const now = new Date();
  return now >= trialStartDate.value && now <= trialEndDate.value;
});
const trialBlocked = computed(() => Boolean(auth.user?.trial_blocked));
const subscriptionBlocked = computed(() => Boolean(auth.user?.subscription_blocked));
const blockedTrialEndDateLabel = computed(() => {
  if (!trialEndDate.value || Number.isNaN(trialEndDate.value.getTime())) {
    return "data indisponível";
  }
  return trialEndDate.value.toLocaleDateString();
});
const blockedTrialDescription = computed(
  () =>
    `Seu trial terminou em ${blockedTrialEndDateLabel.value}. Assine um plano para desbloquear seu painel e voltar a publicar seus roteiros.`
);
const blockedAccessTitle = computed(() =>
  subscriptionBlocked.value ? viewCopy.subscription.blocked : viewCopy.trial.blocked
);
const blockedAccessDescription = computed(() =>
  subscriptionBlocked.value ? viewCopy.subscription.blocked.description : blockedTrialDescription.value
);
const trialDaysLeft = computed(() => {
  if (!trialActive.value || !trialEndDate.value) return null;
  const diff = trialEndDate.value.getTime() - Date.now();
  if (diff <= 0) return 0;
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
});

watch(
  () => [auth.user?.id, trialActive.value, auth.user?.trial_ack_start],
  () => {
    showWelcomeDialog.value = Boolean(trialActive.value && auth.user?.trial_ack_start === false);
  },
  { immediate: true }
);

watch(
  () => route.path,
  () => {
    mobileMenuOpen.value = false;
    scrollToTop();
  }
);

watch(
  () => [trialBlocked.value, subscriptionBlocked.value, route.fullPath],
  () => {
    if (trialBlocked.value || subscriptionBlocked.value) {
      showEndDialog.value = route.path !== "/admin/planos";
    } else {
      showEndDialog.value = false;
    }
  },
  { immediate: true }
);

watch(
  () => [trialActive.value, auth.user?.trial_warn_3days_ack, trialDaysLeft.value],
  () => {
    const daysLeft = trialDaysLeft.value;
    showTrialWarning3Days.value = Boolean(
      trialActive.value && auth.user?.trial_warn_3days_ack === false && daysLeft !== null && daysLeft <= 3 && daysLeft > 1
    );
  },
  { immediate: true }
);

watch(
  () => [trialActive.value, auth.user?.trial_warn_1day_ack, trialDaysLeft.value],
  () => {
    const daysLeft = trialDaysLeft.value;
    showTrialWarning1Day.value = Boolean(
      trialActive.value && auth.user?.trial_warn_1day_ack === false && daysLeft !== null && daysLeft <= 1
    );
  },
  { immediate: true }
);

const goToPlans = () => {
  router.push("/admin/planos");
};

const acknowledgeTrial = async (stage: "start" | "end" | "warn3" | "warn1", redirectToPlans = false) => {
  try {
    await api.post("/auth/trial/ack", { stage });
    await auth.fetchProfile();
    if (stage === "start") {
      showWelcomeDialog.value = false;
    } else if (stage === "warn3") {
      showTrialWarning3Days.value = false;
    } else if (stage === "warn1") {
      showTrialWarning1Day.value = false;
      showTrialWarning3Days.value = false;
    } else {
      showEndDialog.value = false;
    }
    if (redirectToPlans) {
      goToPlans();
    }
  } catch (err) {
    console.error("Erro ao confirmar trial", err);
  }
};

const ensureAgencySelection = (id: number | null) => {
  if (!id) return;
  agencyStore.currentAgencyId = id;
};

const isSlugInUseError = (detail?: string | null) => {
  if (!detail) return false;
  const normalized = detail.toLowerCase();
  return normalized.includes("slug") && (normalized.includes("uso") || normalized.includes("use"));
};

type AgencyPayload = {
  name: string;
  primary_color?: string | null;
  secondary_color?: string | null;
  logo_url?: string | null;
  cta_whatsapp?: string | null;
};

const createAgencyWithSlugFallback = async (payload: AgencyPayload) => {
  const baseSlug = slugify(payload.name, "agencia");
  const maxAttempts = 8;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const suffix = attempt === 0 ? "" : `-${attempt}`;
    const slugCandidate = `${baseSlug}${suffix}`;
    try {
      const res = await api.post("/agencies", { ...payload, slug: slugCandidate });
      return res;
    } catch (err) {
      const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
      if (isSlugInUseError(detail)) continue;
      throw err;
    }
  }
  throw new Error(viewCopy.onboarding.errors.slugUnavailable);
};

const upsertAgencyDuringSetup = async (name: string) => {
  const payload: AgencyPayload = {
    name,
    primary_color: agencySetupForm.primary_color || DEFAULT_AGENCY_COLOR,
    secondary_color: agencySetupForm.secondary_color || null,
    logo_url: agencySetupForm.logo_url || null,
    cta_whatsapp: ""
  };
  if (!agencySetupCreatedId.value) {
    const res = await createAgencyWithSlugFallback(payload);
    const createdId = res.data?.id ?? null;
    agencySetupCreatedId.value = createdId;
    await agencyStore.loadAgencies();
    ensureAgencySelection(createdId);
    return createdId;
  }
  const targetId = agencySetupCreatedId.value;
  await api.put(`/agencies/${targetId}`, {
    ...payload,
    slug: slugify(name, "agencia")
  });
  await agencyStore.loadAgencies();
  ensureAgencySelection(targetId);
  return targetId;
};

const startAgencySetupFlow = async () => {
  await acknowledgeTrial("start");
  resetAgencySetupForm();
  showAgencySetupFlow.value = true;
};

const goToNextAgencySetupStep = async () => {
  if (agencySetupStepLoading.value) return;
  agencySetupError.value = "";
  if (agencySetupStep.value === "name") {
    const trimmed = agencySetupForm.name.trim();
    if (!trimmed) {
      agencySetupError.value = viewCopy.onboarding.errors.missingName;
      return;
    }
    agencySetupForm.name = trimmed;
    agencySetupStepLoading.value = true;
    try {
      await upsertAgencyDuringSetup(trimmed);
      agencySetupStep.value = "logo";
    } catch (err) {
      console.error(err);
      const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
      agencySetupError.value = detail || viewCopy.onboarding.errors.cannotAdvance;
    } finally {
      agencySetupStepLoading.value = false;
    }
    return;
  }
  if (agencySetupStep.value === "logo") {
    agencySetupStep.value = "color";
  }
};

const goToPreviousAgencySetupStep = () => {
  agencySetupError.value = "";
  if (agencySetupStep.value === "logo") {
    agencySetupStep.value = "name";
  } else if (agencySetupStep.value === "color") {
    agencySetupStep.value = "logo";
  }
};

const closeAgencySetupFlow = () => {
  showAgencySetupFlow.value = false;
  showAgencySetupUnsavedDialog.value = false;
  resetAgencySetupForm();
};

const requestAgencySetupClose = () => {
  if (agencySetupStepLoading.value || agencySetupSaving.value) return;
  if (agencySetupDirty.value) {
    showAgencySetupUnsavedDialog.value = true;
    return;
  }
  closeAgencySetupFlow();
};

const keepAgencySetupEditing = () => {
  showAgencySetupUnsavedDialog.value = false;
};

const confirmAgencySetupDiscard = () => {
  showAgencySetupUnsavedDialog.value = false;
  closeAgencySetupFlow();
};

const submitAgencySetup = async () => {
  if (agencySetupSaving.value) return;
  agencySetupError.value = "";
  const trimmed = agencySetupForm.name.trim();
  if (!trimmed) {
    agencySetupStep.value = "name";
    agencySetupError.value = viewCopy.onboarding.errors.missingName;
    return;
  }

  const payload: AgencyPayload = {
    name: trimmed,
    logo_url: agencySetupForm.logo_url || null,
    primary_color: agencySetupForm.primary_color || DEFAULT_AGENCY_COLOR,
    secondary_color: agencySetupForm.secondary_color || null,
    cta_whatsapp: ""
  };

  try {
    agencySetupSaving.value = true;
    let agencyId = agencySetupCreatedId.value;
    if (!agencyId) {
      const res = await createAgencyWithSlugFallback(payload);
      agencyId = res.data?.id ?? null;
      agencySetupCreatedId.value = agencyId;
    } else {
      await api.put(`/agencies/${agencyId}`, {
        ...payload,
        slug: slugify(trimmed, "agencia")
      });
    }
    await agencyStore.loadAgencies();
    ensureAgencySelection(agencyId ?? null);
    if (auth.user?.email) {
      await addTagsToContactByEmail(auth.user.email, [viajeChatTagIds.AGENCIA_CRIADA]);
    }
    agencySetupStep.value = "success";
    agencySetupError.value = "";
    markAgencySetupSnapshot();
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
    agencySetupError.value = detail || viewCopy.onboarding.errors.cannotCreateAgency;
  } finally {
    agencySetupSaving.value = false;
  }
};

const createFirstPageFromOnboarding = async () => {
  if (!agencyStore.currentAgencyId && agencySetupCreatedId.value) {
    ensureAgencySelection(agencySetupCreatedId.value);
  }
  if (!agencyStore.currentAgencyId) {
    createFirstPageError.value = viewCopy.onboarding.errors.mustCreateAgency;
    return;
  }
  createFirstPageError.value = "";
  try {
    createFirstPageLoading.value = true;
    const slug = slugify(`${agencySetupForm.name || "pagina"}-inicial`, "pagina");
    const res = await api.post<{ id: number }>("/pages", {
      agency_id: agencyStore.currentAgencyId,
      title: viewCopy.onboarding.firstPageTitle,
      slug,
      status: "draft"
    });
    closeAgencySetupFlow();
    router.push(`/admin/pages/${res.data.id}/edit`);
  } catch (err) {
    console.error(err);
    const detail = (err as any)?.response?.data?.detail || (err as Error)?.message;
    createFirstPageError.value = detail || viewCopy.onboarding.errors.cannotCreatePage;
  } finally {
    createFirstPageLoading.value = false;
  }
};

const formattedDate = computed(() => (trialEndDate.value ? trialEndDate.value.toLocaleDateString() : ""));
const scrollToTop = () => {
  if (typeof window === "undefined") return;
  window.scrollTo({ top: 0, behavior: "auto" });
};

onMounted(async () => {
  setupViewportWatcher();
  if (auth.token && !auth.user) {
    await auth.ensureHydrated().catch(() => undefined);
  }
  if (!agencyStore.agencies.length) {
    await agencyStore.loadAgencies();
  }
  if (!agencyStore.currentAgencyId && agencyStore.agencies.length) {
    agencyStore.currentAgencyId = agencyStore.agencies[0].id;
  }
  if (!auth.user && auth.token) {
    await auth.fetchProfile();
  }
  checkCookieConsent();
  scrollToTop();
});

onBeforeUnmount(() => {
  if (removeViewportWatcher) {
    removeViewportWatcher();
  }
  if (hasWindow) {
    document.body.classList.remove(bodyDarkClass, bodyLightClass);
  }
});

watch(
  () => agencyStore.agencies.length,
  length => {
    if (!agencyStore.currentAgencyId && length > 0) {
      agencyStore.currentAgencyId = agencyStore.agencies[0].id;
    }
  }
);

const queuePlanTagSync = (plan: string | null | undefined) => {
  const email = auth.user?.email;
  if (!email) return;
  const normalizedPlan = plan ?? null;
  const desiredTagId = normalizedPlan ? planTagMap[normalizedPlan] ?? null : null;
  planTagSyncQueue = planTagSyncQueue
    .catch(() => {})
    .then(async () => {
      await syncPlanTagForEmail(email, desiredTagId ?? null, planTagIds);
      lastSyncedPlan.value = normalizedPlan;
    });
};

watch(
  () => auth.user?.plan,
  plan => {
    const normalizedPlan = plan ?? null;
    if (normalizedPlan === lastSyncedPlan.value) return;
    queuePlanTagSync(normalizedPlan);
  },
  { immediate: true }
);

watch(
  () => auth.user?.email,
  () => {
    lastSyncedPlan.value = null;
  }
);
</script>
<style>
/* =========================
   SCALE GLOBAL CORRIGIDO
========================= */

.admin-scale-85 {
  zoom: 0.85;
  min-height: 100vh;
}

  .admin-scale-85 {
  min-height: 100vh;
}


/* =========================
   ROOT / FUNDO GLOBAL
========================= */

html,
body,
#app {
  min-height: 100%;
}

body.admin-body-dark {
  background-color: #05070f;
}

body.admin-body-light {
  background-color: #f8fafc;
}


/* =========================
   THEMES
========================= */

.light-theme {
  background: #f8fafc;
  color: #0f172a;
}

.dark-theme {
  background: #020617;
  color: #f1f5f9;
}


/* =========================
   ADMIN LAYOUT FIX
========================= */

.admin-main {
  min-height: 0;
  height: 100%;
}

.admin-content {
  display: flex;
  flex-direction: column;
  min-height: 0;
}


/* =========================
   DARK MODE OVERRIDES
========================= */

.dark-theme .admin-main {
  background: #05070f;
  color: #f1f5f9;
}

.dark-theme .admin-content {
  color: #f1f5f9;
}

.dark-theme .bg-white,
.dark-theme .bg-slate-50,
.dark-theme .bg-slate-100,
.dark-theme .bg-gray-50,
.dark-theme .bg-slate-200 {
  background-color: #202020;
  color: #f1f5f9;
}

.dark-theme .bg-white\/90 {
  background-color: rgba(32, 32, 32, 0.92);
  color: #f1f5f9;
}

.dark-theme .bg-white\/20,
.dark-theme .bg-white\/15,
.dark-theme .bg-white\/10,
.dark-theme .bg-white\/5 {
  background-color: rgba(255, 255, 255, 0.08);
  color: #f1f5f9;
}


/* =========================
   TEXT COLORS
========================= */

.dark-theme .text-slate-900,
.dark-theme .text-slate-800 {
  color: #f8fafc;
}

.dark-theme .text-slate-700,
.dark-theme .text-slate-600 {
  color: #e2e8f0;
}

.dark-theme .text-slate-500,
.dark-theme .text-slate-400 {
  color: #f5f5f5;
}


/* =========================
   BORDERS / RINGS
========================= */

.dark-theme .border-slate-100,
.dark-theme .border-slate-200,
.dark-theme .border-slate-300 {
  border-color: rgba(148, 163, 184, 0.5);
}

.dark-theme .ring-slate-100,
.dark-theme .ring-slate-200 {
  --tw-ring-color: rgba(148, 163, 184, 0.4);
}


/* =========================
   INPUTS
========================= */

.dark-theme input,
.dark-theme textarea,
.dark-theme select {
  background-color: #020617;
  color: #f1f5f9;
  border-color: rgba(148, 163, 184, 0.6);
}


/* =========================
   SHADOW
========================= */

.dark-theme .shadow,
.dark-theme .shadow-md,
.dark-theme .shadow-lg,
.dark-theme .shadow-inner {
  --tw-shadow-color: rgba(0, 0, 0, 0.6);
}


/* =========================
   TOGGLE
========================= */

.toggle-knob {
  background-color: #ffffff !important;
}


/* =========================
   ANIMATION
========================= */

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>













