<template>
  <div
    :class="[
      'admin-shell-root min-h-screen overflow-x-clip bg-background text-[14px] text-foreground',
      isPlansRoute ? 'plans-layout bg-white text-slate-900' : '',
      isAdminMasterRoute ? 'is-admin-master' : '',
      themeWrapperClass
    ]"
  >
    <div v-if="showAuthSplash" class="flex min-h-screen items-center justify-center">
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
    <div class="flex min-h-screen">
      <aside
        :class="['admin-sidebar hidden md:flex', { 'is-collapsed': sidebarCompact, 'is-unpinned': sidebarCollapsed, 'is-peek': sidebarCollapsed && sidebarPeek && !isAdminMasterRoute, 'is-master': isAdminMasterRoute }]"
        :aria-label="t({ pt: 'Menu principal', es: 'Menú principal' })"
        @mouseenter="peekSidebar(true)"
        @mouseleave="peekSidebar(false)"
        @focusin="peekSidebar(true)"
        @focusout="handleSidebarFocusOut"
      >
        <div class="as-panel" @mouseover="showSidebarTip" @mouseleave="hideSidebarTip" @focusin="showSidebarTip" @focusout="hideSidebarTip">
          <div class="as-brand">
            <BrandSwitcher
              v-if="viajeonLoginReady"
              :compact="sidebarCompact"
              :loading="viajeonSsoLoading"
              @select-viajeon="openViajeonPanel"
            />
            <RouterLink
              v-else
              to="/admin/dashboard"
              :class="sidebarCompact ? 'as-brand-tile' : 'as-brand-logo'"
              aria-label="Ir para o início"
            >
              <img v-if="sidebarCompact" :src="brandMarkSrc" alt="Roteiro Online" class="h-7 w-7 object-contain" />
              <img v-else :src="mobileHeaderLogoSrc" alt="Roteiro Online" class="as-logo-img" />
            </RouterLink>
            <button
              v-if="!isAdminMasterRoute"
              type="button"
              class="as-pin"
              :class="{ 'is-pinned': !sidebarCollapsed }"
              :aria-label="sidebarCollapsed ? t({ pt: 'Fixar menu', es: 'Fijar menú' }) : t({ pt: 'Desafixar menu', es: 'Soltar menú' })"
              :title="sidebarCollapsed ? t({ pt: 'Fixar menu', es: 'Fijar menú' }) : t({ pt: 'Desafixar menu (abre ao passar o mouse)', es: 'Soltar menú (se abre al pasar el mouse)' })"
              :aria-pressed="!sidebarCollapsed"
              @click="toggleSidebarCollapsed"
            >
              <PinIcon v-if="!sidebarCollapsed" aria-hidden="true" />
              <PinOffIcon v-else aria-hidden="true" />
            </button>
          </div>

          <RouterLink
            v-if="canCreatePageShortcut"
            :to="{ path: '/admin/pages', query: { nova: '1' } }"
            class="as-cta"
            :aria-label="t({ pt: 'Nova página', es: 'Nueva página' })"
            :data-tip="sidebarCompact ? t({ pt: 'Nova página', es: 'Nueva página' }) : null"
          >
            <span class="as-cta-icon"><PlusIcon aria-hidden="true" /></span>
            <span class="as-label">{{ t({ pt: "Nova página", es: "Nueva página" }) }}</span>
          </RouterLink>

          <nav class="as-nav sidebar-scroll" @scroll.passive="closeSidebarFlyout">
            <section
              v-for="section in sidebarSections"
              :key="`desktop-section-${section.id}`"
              class="as-section"
            >
              <p class="as-section-title">{{ section.label }}</p>
              <template v-for="item in section.items" :key="item.id">
                <RouterLink
                  v-if="item.type === 'link'"
                  :to="item.to"
                  class="as-item"
                  :class="{ 'is-active': isTopLevelActive(item) }"
                  :aria-label="item.label"
                  :data-tip="sidebarCompact ? item.label : null"
                >
                  <span class="as-icon"><component :is="navIconFor(item.iconPath)" aria-hidden="true" /></span>
                  <span class="as-label">{{ item.label }}</span>
                  <span v-if="!sidebarCompact && item.id === 'admin-master'" class="nav-master-badge">MASTER</span>
                  <span v-if="!sidebarCompact && getNavBadge(item.id) !== null" class="nav-pill-badge">{{ getNavBadge(item.id) }}</span>
                </RouterLink>
                <div v-else class="as-group">
                  <button
                    type="button"
                    class="as-item"
                    :class="{ 'is-active': isParentActive(item), 'is-open': sidebarCompact && flyoutGroupId === item.id }"
                    :aria-label="item.label"
                    :aria-expanded="sidebarCompact ? flyoutGroupId === item.id : isGroupExpanded(item)"
                    :data-tip="sidebarCompact && flyoutGroupId !== item.id ? item.label : null"
                    @click.stop="handleGroupClick(item.id, $event)"
                  >
                    <span class="as-icon"><component :is="navIconFor(item.iconPath)" aria-hidden="true" /></span>
                    <span class="as-label">{{ item.label }}</span>
                    <ChevronDownIcon
                      v-if="!sidebarCompact"
                      class="as-chevron"
                      :class="{ 'rotate-180': isGroupExpanded(item) }"
                      aria-hidden="true"
                    />
                  </button>
                  <div v-if="!sidebarCompact && isGroupExpanded(item)" class="as-children">
                    <RouterLink
                      v-for="child in item.children"
                      :key="`${item.id}-${child.path}`"
                      :to="child.path"
                      class="as-child"
                      :class="{ 'is-active': isChildActive(child.path) }"
                    >
                      {{ child.label }}
                    </RouterLink>
                  </div>
                  <Teleport to="body">
                  <transition name="as-flyout">
                    <div
                      v-if="sidebarCompact && flyoutGroupId === item.id"
                      class="as-flyout"
                      role="menu"
                      :style="{ top: `${flyoutTop}px`, left: `${flyoutLeft}px` }"
                      @click.stop
                    >
                      <p class="as-flyout-title">{{ item.label }}</p>
                      <RouterLink
                        v-for="child in item.children"
                        :key="`flyout-${item.id}-${child.path}`"
                        :to="child.path"
                        class="as-child"
                        :class="{ 'is-active': isChildActive(child.path) }"
                        role="menuitem"
                        @click="flyoutGroupId = null"
                      >
                        {{ child.label }}
                      </RouterLink>
                    </div>
                  </transition>
                  </Teleport>
                </div>
              </template>
            </section>
          </nav>

          <div class="as-footer">
            <button
              type="button"
              class="as-item"
              :aria-label="viewCopy.themeToggle.label"
              :data-tip="sidebarCompact ? (isDarkTheme ? viewCopy.themeToggle.title + ': ' + viewCopy.themeToggle.active : viewCopy.themeToggle.title) : null"
              @click="toggleTheme"
            >
              <span class="as-icon">
                <SunIcon v-if="isDarkTheme" aria-hidden="true" />
                <MoonIcon v-else aria-hidden="true" />
              </span>
              <span class="as-label">{{ viewCopy.themeToggle.title }}</span>
              <span v-if="!sidebarCompact" class="as-switch" :class="{ on: isDarkTheme }" aria-hidden="true"><span></span></span>
            </button>
            <div class="as-user">
              <RouterLink
                to="/admin/perfil"
                class="as-user-link"
                :aria-label="userDisplayName || 'Perfil'"
                :data-tip="sidebarCompact ? (userDisplayName || 'Perfil') : null"
              >
                <span class="as-avatar">
                  <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="" class="h-full w-full object-cover" />
                  <template v-else>{{ userInitial }}</template>
                </span>
                <span class="as-label as-user-text">
                  <span class="block truncate text-[13px] font-semibold text-foreground">{{ (userDisplayName || "").split(" ")[0] || userDisplayName }}</span>
                  <span class="block text-[11px] text-muted-foreground">{{ userRoleLabel }}</span>
                </span>
              </RouterLink>
              <button
                v-if="!sidebarCompact"
                type="button"
                class="as-logout"
                :aria-label="viewCopy.sidebar.logout"
                :title="viewCopy.sidebar.logout"
                @click="handleLogout"
              >
                <LogOutIcon aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </aside>
      <Teleport to="body">
        <div
          v-if="sidebarCompact && sidebarTip.text"
          class="as-tip"
          role="tooltip"
          :style="{ top: `${sidebarTip.top}px`, left: `${sidebarTip.left}px` }"
        >{{ sidebarTip.text }}</div>
      </Teleport>
      <main
        :class="[
          'admin-main flex min-h-0 min-w-0 flex-1 flex-col overflow-x-clip bg-background text-foreground',
          isPlansRoute ? 'bg-white text-slate-900' : ''
        ]"
      >
        <div v-if="!isPageEditorRoute" class="mobile-topbar md:hidden">
          <header class="mobile-topbar-card">
            <RouterLink to="/admin/dashboard" class="flex min-w-0 items-center" aria-label="Ir para o início">
              <img :src="mobileHeaderLogoSrc" alt="Roteiro Online" class="as-logo-img" />
            </RouterLink>
            <button
              type="button"
              class="inline-flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl text-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              @click="mobileMenuOpen = true"
              aria-label="Abrir menu"
              title="Abrir menu"
            >
              <MenuIcon class="h-6 w-6" aria-hidden="true" />
            </button>
          </header>
        </div>
        <div
          :class="[
            isInboxRoute
              ? 'admin-content flex-1 min-h-0 overflow-hidden bg-inherit p-0'
              : isPageEditorRoute
                ? 'admin-content flex-1 min-h-0 overflow-x-clip bg-background p-2 lg:overflow-y-auto'
              : isPlansRoute
                ? 'admin-content flex-1 min-h-0 overflow-hidden overflow-x-hidden bg-white p-0'
                : 'admin-content flex-1 min-h-0 overflow-y-auto overflow-x-hidden bg-background px-4 pb-6 pt-2.5 sm:px-6 md:py-6 lg:px-8',
            isPlansRoute
              ? 'bg-white text-slate-900'
              : 'text-foreground'
          ]"
        >
          <div
            :class="[
              isPlansRoute ? 'flex-1 min-h-0 bg-white overflow-hidden' : 'flex-1 min-h-0 bg-background',
              isFramedRoute ? 'admin-page-frame mx-auto w-full max-w-[1400px]' : ''
            ]"
          >
            <div v-if="isAdminMasterRoute" class="admin-master-shell">
              <AdminMasterNav class="admin-master-rail" />
              <div class="admin-master-main"><RouterView /></div>
            </div>
            <RouterView v-else />
          </div>
        </div>
      </main>
    </div>
    </template>

    <transition name="mobile-sidebar">
      <div
        v-if="mobileMenuOpen"
        class="mobile-menu fixed inset-0 z-50 flex justify-end md:hidden"
      >
        <div class="mobile-menu-overlay" @click="mobileMenuOpen = false"></div>
        <div class="mobile-menu-panel" role="dialog" aria-modal="true" :aria-label="t({ pt: 'Menu', es: 'Menú' })">
          <div class="mobile-menu-head">
            <h2 class="font-display text-lg font-bold tracking-tight text-foreground">Menu</h2>
            <button
              type="button"
              class="mobile-menu-close"
              @click="mobileMenuOpen = false"
              :aria-label="viewCopy.sidebar.closeMenu"
              :title="viewCopy.sidebar.closeMenu"
            >
              <XIcon aria-hidden="true" />
            </button>
          </div>
          <RouterLink
            v-if="canCreatePageShortcut"
            :to="{ path: '/admin/pages', query: { nova: '1' } }"
            class="as-cta"
            @click="mobileMenuOpen = false"
          >
            <span class="as-cta-icon"><PlusIcon aria-hidden="true" /></span>
            <span class="as-label">{{ t({ pt: "Nova página", es: "Nueva página" }) }}</span>
          </RouterLink>
          <nav class="as-nav sidebar-scroll">
            <section
              v-for="section in sidebarSections"
              :key="`mobile-section-${section.id}`"
              class="as-section"
            >
              <p class="as-section-title">{{ section.label }}</p>
              <template v-for="item in section.items" :key="'mobile-' + item.id">
                <RouterLink
                  v-if="item.type === 'link'"
                  :to="item.to"
                  class="as-item"
                  :class="{ 'is-active': isTopLevelActive(item) }"
                  @click="mobileMenuOpen = false"
                >
                  <span class="as-icon"><component :is="navIconFor(item.iconPath)" aria-hidden="true" /></span>
                  <span class="as-label">{{ item.label }}</span>
                  <span v-if="item.id === 'admin-master'" class="nav-master-badge">MASTER</span>
                  <span v-if="getNavBadge(item.id) !== null" class="nav-pill-badge">{{ getNavBadge(item.id) }}</span>
                </RouterLink>
                <div v-else class="as-group">
                  <button
                    type="button"
                    class="as-item"
                    :class="{ 'is-active': isParentActive(item) }"
                    :aria-expanded="isGroupExpanded(item)"
                    @click="toggleNavGroup(item.id)"
                  >
                    <span class="as-icon"><component :is="navIconFor(item.iconPath)" aria-hidden="true" /></span>
                    <span class="as-label">{{ item.label }}</span>
                    <ChevronDownIcon class="as-chevron" :class="{ 'rotate-180': isGroupExpanded(item) }" aria-hidden="true" />
                  </button>
                  <div v-if="isGroupExpanded(item)" class="as-children">
                    <RouterLink
                      v-for="child in item.children"
                      :key="'mobile-' + item.id + '-' + child.path"
                      :to="child.path"
                      class="as-child"
                      :class="{ 'is-active': isChildActive(child.path) }"
                      @click="mobileMenuOpen = false"
                    >
                      {{ child.label }}
                    </RouterLink>
                  </div>
                </div>
              </template>
            </section>
          </nav>
          <div class="as-footer">
            <button
              type="button"
              class="as-item"
              :aria-label="viewCopy.themeToggle.label"
              @click="toggleTheme"
            >
              <span class="as-icon">
                <SunIcon v-if="isDarkTheme" aria-hidden="true" />
                <MoonIcon v-else aria-hidden="true" />
              </span>
              <span class="as-label">{{ viewCopy.themeToggle.title }}</span>
              <span class="as-switch" :class="{ on: isDarkTheme }" aria-hidden="true"><span></span></span>
            </button>
            <div class="as-user">
              <RouterLink
                to="/admin/perfil"
                class="as-user-link"
                :aria-label="userDisplayName || 'Perfil'"
                @click="mobileMenuOpen = false"
              >
                <span class="as-avatar">
                  <img v-if="userAvatarUrl" :src="userAvatarUrl" alt="" class="h-full w-full object-cover" />
                  <template v-else>{{ userInitial }}</template>
                </span>
                <span class="as-label as-user-text">
                  <span class="block truncate text-[13px] font-semibold text-foreground">{{ (userDisplayName || "").split(" ")[0] || userDisplayName }}</span>
                  <span class="block text-[11px] text-muted-foreground">{{ userRoleLabel }}</span>
                </span>
              </RouterLink>
              <button
                type="button"
                class="as-logout"
                :aria-label="viewCopy.sidebar.logout"
                :title="viewCopy.sidebar.logout"
                @click="handleLogout"
              >
                <LogOutIcon aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="showWelcomeDialog"
        class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4"
      >
        <div class="w-full max-w-lg rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-elegant sm:p-8">
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
        class="app-modal-overlay fixed inset-0 z-[60] flex items-center justify-center px-4 py-6"
      >
        <div class="w-full max-w-2xl rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-elegant sm:p-8">
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
                <CheckIcon class="h-8 w-8" aria-hidden="true" />
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
        class="app-modal-overlay fixed inset-0 z-[70] flex items-center justify-center px-4"
      >
        <div class="w-full max-w-md rounded-2xl border border-border bg-card p-6 text-center text-card-foreground shadow-elegant">
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
        class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4"
      >
        <div class="w-full max-w-lg rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-elegant sm:p-8">
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
        class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4"
      >
        <div class="w-full max-w-lg rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-elegant sm:p-8">
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
        class="app-modal-overlay fixed inset-0 z-50 flex items-center justify-center px-4"
      >
        <div class="w-full max-w-lg rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-elegant sm:p-8">
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
        v-if="showSubscriptionBlockedDialog"
        class="app-modal-overlay fixed inset-0 z-[55] flex items-center justify-center px-4"
      >
        <div class="w-full max-w-lg rounded-2xl border border-border bg-card p-6 text-card-foreground shadow-elegant sm:p-8">
          <p class="text-xs font-semibold uppercase tracking-[0.3em] text-rose-500">{{ viewCopy.subscription.blocked.eyebrow }}</p>
          <h2 class="mt-3 text-2xl font-bold text-slate-900">{{ viewCopy.subscription.blocked.title }}</h2>
          <p class="mt-2 text-sm text-slate-600">{{ viewCopy.subscription.blocked.description }}</p>
          <div class="mt-6 flex flex-wrap justify-end">
            <button
              class="rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              @click="goToPlansFromSubscriptionBlock"
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
        <div class="flex flex-col gap-2 rounded-2xl border border-border bg-card p-4 text-card-foreground shadow-elegant">
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

    <transition name="fade">
      <div
        v-if="permissionSnackbar.open"
        class="app-snackbar-layer fixed bottom-4 left-1/2 z-[1000] w-[calc(100%-2rem)] max-w-xl -translate-x-1/2 md:bottom-6 md:w-auto md:min-w-[360px]"
      >
        <div class="rounded-xl bg-destructive px-4 py-3 text-sm font-semibold text-destructive-foreground shadow-elegant">
          {{ permissionSnackbar.message }}
        </div>
      </div>
    </transition>
    <transition name="fade">
      <button
        v-if="floatingInboxNotification.open"
        type="button"
        class="fixed right-5 top-5 z-[1100] w-[calc(100%-2.5rem)] max-w-sm rounded-2xl border border-border bg-card p-3 text-left text-card-foreground shadow-elegant transition hover:-translate-y-[1px]"
        @click="openInboxFromNotification"
      >
        <p class="text-[11px] font-semibold uppercase tracking-wide text-emerald-600">Nova mensagem</p>
        <p class="mt-1 truncate text-sm font-semibold text-slate-900">{{ floatingInboxNotification.title }}</p>
        <p class="mt-0.5 truncate text-xs text-slate-600">
          <template v-if="floatingInboxNotification.groupSender">
            <strong>{{ floatingInboxNotification.groupSender }}:</strong> {{ floatingInboxNotification.body }}
          </template>
          <template v-else>{{ floatingInboxNotification.body }}</template>
        </p>
      </button>
    </transition>

    <a
      v-if="!isEditorRoute && !mobileMenuOpen"
      href="https://wa.me/5553991800903"
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
// Estilos das telas do Admin Master: só o painel baixa (a página pública não usa).
import "../styles/admin-master.css";
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import type { Component } from "vue";
import {
  BadgePercentIcon,
  Building2Icon,
  CheckIcon,
  ChevronDownIcon,
  PinIcon,
  PinOffIcon,
  CircleIcon,
  FileTextIcon,
  GlobeIcon,
  GraduationCapIcon,
  LifeBuoyIcon,
  LayoutDashboardIcon,
  Link2Icon,
  LogOutIcon,
  MenuIcon,
  MessagesSquareIcon,
  MoonIcon,
  PlugIcon,
  PlusIcon,
  ShieldCheckIcon,
  SunIcon,
  UserRoundIcon,
  UsersIcon,
  XIcon
} from "lucide-vue-next";
import BrandMark from "../assets/Favicon.png";
import AdminMasterNav from "../components/admin/master/AdminMasterNav.vue";
import SidebarLogo from "../assets/Logo Branco - Roteiro Online.png";
import ColoredLogo from "../assets/Logo Cor - Roteiro Online.png";
import BrandSwitcher from "../components/shared/BrandSwitcher.vue";
import ImageUploadField from "../components/admin/inputs/ImageUploadField.vue";
import api, { API_PERMISSION_DENIED_EVENT } from "../services/api";
import { getWhatsAppInboxAccess, listWhatsAppConversations } from "../services/whatsapp";
import type { WhatsAppConversation } from "../types/whatsapp";
import { API_ROOT_URL } from "../utils/apiBase";
import { useAgencyStore } from "../store/useAgencyStore";
import { useAuthStore } from "../store/useAuthStore";
import { useLeadCaptureStore } from "../store/useLeadCaptureStore";
import { useThemeStore } from "../store/useThemeStore";
import { getPlanLabel } from "../utils/planLabels";
import { addTagsToContactByEmail, syncPlanTagForEmail, viajeChatTagIds } from "../services/viajeChat";
import { normalizeAgencySlugInput, slugify } from "../utils/slugify";
import { createAdminLocalizer } from "../utils/adminI18n";
import { canAccessPermission, type PermissionKey } from "../utils/permissions";

const route = useRoute();
const router = useRouter();
const agencyStore = useAgencyStore();
const auth = useAuthStore();
const leadStore = useLeadCaptureStore();
const routeRequiresAuth = computed(() => route.matched.some(record => record.meta?.requiresAuth));
const isInboxRoute = computed(() => route.path.startsWith("/admin/inbox"));
// O editor de páginas usa a tela quase inteira: só uma borda fina em volta.
const isPageEditorRoute = computed(() => route.name === "page-edit");
const isPlansRoute = computed(() => route.name === "plans");
const isAdminMasterRoute = computed(() => route.path.startsWith("/admin/administracao"));
// No editor de página a tela é toda do editor: sem o botão de ajuda do WhatsApp.
const isEditorRoute = computed(() => route.name === "page-edit");
// Telas comuns ficam num contêiner único (largura máxima de 1400px, como no Viaje On).
// Editor, Inbox, Planos e Admin Master têm molduras próprias.
const isFramedRoute = computed(
  () => !isInboxRoute.value && !isPageEditorRoute.value && !isPlansRoute.value && !isAdminMasterRoute.value
);
const showAuthSplash = computed(() => {
  if (!routeRequiresAuth.value) return false;
  if (!auth.token) return false;
  return auth.isHydrating || !auth.user;
});
const navPageCount = ref<number | null>(null);
const navLeadCount = ref<number | null>(null);
const permissionSnackbar = ref({ open: false, message: "" });
let permissionSnackbarTimer: number | null = null;
const viajeonConnected = ref(false);
const viajeonSsoEmail = ref("");
const viajeonSsoLoading = ref(false);
const viajeonLoginReady = computed(() => viajeonConnected.value && Boolean(viajeonSsoEmail.value.trim()));
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
const userAvatarUrl = computed(() => {
  const user = auth.user as Record<string, unknown> | null;
  const raw = (user?.avatar_url as string) || "";
  return raw.trim() || null;
});
const userRoleLabel = computed(() => {
  const role = String(auth.user?.role || "").toLowerCase();
  if (auth.user?.is_superuser || role === "admin" || role === "owner" || auth.user?.is_owner) {
    return "Admin";
  }
  if (role === "member" || role === "membro") {
    return "Membro";
  }
  return "Usuário";
});
const themeStore = useThemeStore();
const COOKIE_KEY = "global_cookie_consent";
const t = createAdminLocalizer();

const navCopy = {
  dashboard: { pt: "Dashboard", es: "Dashboard" },
  adminMaster: { pt: "Admin master", es: "Admin master" },
  pages: { pt: "P\u00E1ginas", es: "P\u00E1ginas" },
  leads: { pt: "Leads", es: "Leads" },
  inbox: { pt: "Inbox", es: "Inbox" },
  clients: { pt: "Clientes", es: "Clientes" },
  integrations: { pt: "Integra\u00E7\u00F5es", es: "Integraciones" },
  tracking: { pt: "Rastreamento", es: "Rastreo" },
  viajeon: { pt: "Viaje On", es: "Viaje On" },
  connections: { pt: "Notificações", es: "Atención" },
  domains: { pt: "Dom\u00EDnios", es: "Dominios" },
  agency: { pt: "Minha Ag\u00EAncia", es: "Mi Agencia" },
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
    menuLabel: t({ pt: "Menu", es: "Men\u00FA" }),
    openMenu: t({ pt: "Abrir menu", es: "Abrir men\u00FA" }),
    closeMenu: t({ pt: "Fechar", es: "Cerrar" })
  },
  support: {
    prompt: t({ pt: "Precisa de ajuda?", es: "\u00BFNecesita ayuda?" })
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
      }),
      close: t({ pt: "Fechar", es: "Cerrar" })
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
      description: t({ pt: "Envie o arquivo da sua marca. Você pode trocar depois.", es: "Sube el archivo de tu marca. Puedes cambiarlo después." }),
      fieldLabel: t({ pt: "Logo", es: "Logo" }),
      hint: t({ pt: "Formatos permitidos: JPG e PNG - Tamanho máximo: 10MB", es: "Formatos permitidos: JPG y PNG - Tamaño máximo: 10MB" }),
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
      eyebrow: t({ pt: "Atenção", es: "Atención" }),
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

// Ícones do menu: Lucide, mesma família e espessura em todo o painel.
const navIconComponents: Record<string, Component> = {
  "/admin/dashboard": LayoutDashboardIcon,
  "/admin/pages": FileTextIcon,
  "/admin/leads": UsersIcon,
  "/admin/inbox": MessagesSquareIcon,
  "/admin/clientes": UsersIcon,
  "/admin/integracoes": PlugIcon,
  "/admin/conexoes": Link2Icon,
  "/admin/agency": Building2Icon,
  "/admin/domains": GlobeIcon,
  "/admin/perfil": UserRoundIcon,
  "/admin/planos": BadgePercentIcon,
  "/admin/administracao": ShieldCheckIcon,
  "/admin/aulas": GraduationCapIcon,
  "/admin/ajuda": LifeBuoyIcon
};
const navIconFor = (iconPath: string): Component => navIconComponents[iconPath] || CircleIcon;

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
  /** Marca o item como ativo em qualquer página que comece com este caminho. */
  activeBase?: string;
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
  inbox: navLabel("inbox"),
  "client-detail": navLabel("clients"),
  "admin-management-dashboard": navLabel("dashboard"),
  "admin-management-monitor": t({ pt: "Monitor", es: "Monitor" }),
  "admin-management-users": t({ pt: "Usuários", es: "Usuarios" }),
  "admin-management-global-admin": t({ pt: "Admin global", es: "Admin global" }),
  "admin-management-lessons": t({ pt: "Gestão de aulas", es: "Gestión de cursos" }),
  "admin-management-templates": t({ pt: "Templates", es: "Templates" }),
  "admin-management-flight-apis": t({ pt: "APIs de voo", es: "APIs de vuelo" }),
  "admin-management-banners": t({ pt: "Banners", es: "Banners" }),
  "admin-management-whatsapp": t({ pt: "Gestão WhatsApp", es: "Gestion WhatsApp" }),
  "admin-management-offers": t({ pt: "Ofertas", es: "Ofertas" }),
  "admin-management-webhooks": t({ pt: "Webhooks e Push", es: "Webhooks y Push" }),
  "admin-prompt-constructor": t({ pt: "Prompt Construtor", es: "Prompt Constructor" }),
  "page-edit": t({ pt: "Editar página", es: "Editar página" }),
  lessons: navLabel("lessons"),
  "agency-settings": navLabel("agency"),
  "agency-invoices": t({ pt: "Faturas", es: "Facturas" }),
  "agency-team": "Equipe",
  "agency-domains": navLabel("domains"),
  plans: navLabel("plans"),
  integrations: navLabel("integrations"),
  "integrations-tracking": navLabel("tracking"),
  "integrations-overview": navLabel("integrations"),
  "integrations-viajeon": navLabel("viajeon"),
  "integrations-viajechat": "ViajeChat",
  connections: "WhatsApp",
  profile: navLabel("profile"),
  "admin-management": navLabel("adminMaster")
};
const canAccessCustomDomains = computed(() => true);

const navGroupExpandedState = ref<Record<string, boolean>>({});
const hasPermission = (permission: PermissionKey) =>
  canAccessPermission(permission, {
    isOwner: auth.user?.is_owner,
    selected: auth.user?.permissions || [],
    plan: auth.user?.plan,
    effective: auth.user?.effective_permissions || []
  });
const canManageTeam = computed(() => {
  const isOwner = auth.user?.is_owner ?? true;
  const role = String(auth.user?.role || "admin").toLowerCase();
  return isOwner && (role === "admin" || role === "owner");
});
const inboxEnabled = ref(false);
const normalizePlanKey = (value: string | null | undefined) => {
  const key = String(value || "").trim().toLowerCase();
  if (!key) return "free";
  if (key === "escala" || key === "infinity" || key === "scale") return "scale";
  if (key === "teste" || key === "test") return "test";
  if (key === "growth" || key === "agency" || key === "agencia") return "agency";
  if (key === "essencial" || key === "professional" || key === "trial") return "professional";
  return key;
};
const hasWhatsAppPlanAccess = computed(() => {
  const trial = normalizePlanKey(auth.user?.trial_plan);
  const base = normalizePlanKey(auth.user?.plan);
  const allowed = new Set(["scale", "test", "infinity"]);
  return allowed.has(trial) || allowed.has(base);
});
let inboxFloatingPollTimer: ReturnType<typeof setInterval> | null = null;
let inboxFloatingHideTimer: ReturnType<typeof setTimeout> | null = null;
let inboxWs: WebSocket | null = null;
let inboxWsHeartbeatTimer: ReturnType<typeof setInterval> | null = null;
let inboxWsReconnectTimer: ReturnType<typeof setTimeout> | null = null;
let inboxWsToken = 0;
let inboxWsIntentionalClose = false;
const inboxNotifBootAt = ref<number>(Date.now());
const notifiedInboundMessageIds = ref<string[]>([]);
const lastInboxSnapshot = ref<Record<number, { unread: number; lastAt: string | null }>>({});
const floatingInboxNotification = ref({
  open: false,
  conversationId: 0,
  title: "",
  body: "",
  groupSender: ""
});
const inboxNotifStorageKey = computed(() => {
  const userId = auth.user?.id || "anon";
  const agencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-floating-notif:${userId}:${agencyId}`;
});
const inboxNotifSoundStorageKey = computed(() => {
  const userId = auth.user?.id || "anon";
  const agencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-floating-sound:${userId}:${agencyId}`;
});
const inboxMutedConversationsStorageKey = computed(() => {
  const userId = auth.user?.id || "anon";
  const agencyId = agencyStore.currentAgencyId || "noagency";
  return `inbox-muted-conversations:${userId}:${agencyId}`;
});
const inboxFloatingEnabled = computed(() => {
  try {
    return localStorage.getItem(inboxNotifStorageKey.value) === "1";
  } catch {
    return false;
  }
});
const inboxFloatingSoundEnabled = computed(() => {
  try {
    return localStorage.getItem(inboxNotifSoundStorageKey.value) === "1";
  } catch {
    return false;
  }
});

const isConversationMutedForFloatingNotification = (conversationId: number) => {
  if (!conversationId) return false;
  try {
    const raw = localStorage.getItem(inboxMutedConversationsStorageKey.value);
    if (!raw) return false;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return false;
    return parsed.map(item => Number(item)).some(item => Number.isFinite(item) && item === conversationId);
  } catch {
    return false;
  }
};

const playInboxNotificationSound = () => {
  if (!inboxFloatingSoundEnabled.value) return;
  try {
    const Ctx = (window as any).AudioContext || (window as any).webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.value = 880;
    gain.gain.value = 0.0001;
    osc.connect(gain);
    gain.connect(ctx.destination);
    const now = ctx.currentTime;
    gain.gain.exponentialRampToValueAtTime(0.06, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);
    osc.start(now);
    osc.stop(now + 0.17);
    osc.onended = () => {
      try {
        ctx.close();
      } catch {
        // noop
      }
    };
  } catch {
    // noop
  }
};
const loadInboxAccess = async () => {
  if (!auth.user) {
    inboxEnabled.value = false;
    return;
  }
  try {
    const access = await getWhatsAppInboxAccess(agencyStore.currentAgencyId || auth.user.primary_agency_id || undefined);
    inboxEnabled.value = Boolean(access.enabled);
  } catch {
    inboxEnabled.value = false;
  }
  if (!inboxEnabled.value && route.path.startsWith("/admin/inbox")) {
    router.push({ name: "inbox-unavailable" }).catch(() => {});
  }
};

const showFloatingInboxNotification = (conversation: WhatsAppConversation) => {
  if (isConversationMutedForFloatingNotification(conversation.id)) return;
  const parsedGroup = parseGroupSenderMessage(conversation.remotePhone, conversation.lastMessageText);
  floatingInboxNotification.value = {
    open: true,
    conversationId: conversation.id,
    title: (conversation.remoteName || conversation.remotePhone || "Inbox").trim(),
    body: (parsedGroup?.text || conversation.lastMessageText || "Você recebeu uma nova mensagem.").trim(),
    groupSender: parsedGroup?.sender || ""
  };
  playInboxNotificationSound();
  if (inboxFloatingHideTimer) clearTimeout(inboxFloatingHideTimer);
  inboxFloatingHideTimer = setTimeout(() => {
    floatingInboxNotification.value.open = false;
  }, 7000);
};

const openInboxFromNotification = () => {
  const conversationId = floatingInboxNotification.value.conversationId;
  floatingInboxNotification.value.open = false;
  if (!conversationId) return;
  router.push({ name: "inbox", query: { conversationId: String(conversationId) } }).catch(() => {});
};

const isGroupTarget = (raw: string | null | undefined) => String(raw || "").toLowerCase().endsWith("@g.us");
const parseGroupSenderMessage = (remotePhone: string | null | undefined, text: string | null | undefined) => {
  if (!isGroupTarget(remotePhone)) return null;
  const body = String(text || "");
  const match = body.match(/^\s*\[([^\]]+)\]\s*([\s\S]*)$/);
  if (!match) return null;
  const sender = String(match[1] || "").trim();
  if (!sender) return null;
  return { sender, text: String(match[2] || "").trim() };
};

const pollInboxFloatingNotifications = async () => {
  if (!inboxEnabled.value || !inboxFloatingEnabled.value || !agencyStore.currentAgencyId) return;
  try {
    const rows = await listWhatsAppConversations(agencyStore.currentAgencyId);
    const nextSnapshot: Record<number, { unread: number; lastAt: string | null }> = {};
    const isFirstSnapshot = Object.keys(lastInboxSnapshot.value).length === 0;
    for (const row of rows) {
      const unread = Number(row.unreadCount || 0);
      const lastAt = row.lastMessageAt || row.updatedAt || null;
      nextSnapshot[row.id] = { unread, lastAt };
      const prev = lastInboxSnapshot.value[row.id];
      const hasUnreadIncrease = prev ? unread > prev.unread : false;
      const lastChanged = prev ? prev.lastAt !== lastAt : Boolean(lastAt);
      if (!isFirstSnapshot && hasUnreadIncrease && lastChanged) showFloatingInboxNotification(row);
    }
    lastInboxSnapshot.value = nextSnapshot;
  } catch (err) {
    console.error(err);
  }
};

const resolveWsApiRoot = () => {
  const devWsRoot = (import.meta.env.VITE_WS_API_ROOT || "").trim().replace(/\/$/, "");
  if (devWsRoot) return devWsRoot;
  if (typeof window !== "undefined" && (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")) {
    return "http://localhost:8000";
  }
  const configuredRoot = API_ROOT_URL.replace(/\/$/, "");
  if (typeof window === "undefined") return configuredRoot;
  try {
    const parsed = new URL(configuredRoot);
    if (parsed.host === window.location.host) return window.location.origin.replace(/\/$/, "");
  } catch {
    // noop
  }
  return configuredRoot;
};

const buildInboxWsUrl = () => {
  const token = auth.token;
  const agencyId = agencyStore.currentAgencyId;
  if (!token || !agencyId) return null;
  const wsBase = resolveWsApiRoot().replace(/^http/i, "ws");
  const url = new URL(`${wsBase}/api/v1/whatsapp/ws`);
  url.searchParams.set("token", token);
  url.searchParams.set("agencyId", String(agencyId));
  return url.toString();
};

const disconnectInboxWs = () => {
  inboxWsIntentionalClose = true;
  inboxWsToken += 1;
  if (inboxWsReconnectTimer) {
    clearTimeout(inboxWsReconnectTimer);
    inboxWsReconnectTimer = null;
  }
  if (inboxWsHeartbeatTimer) {
    clearInterval(inboxWsHeartbeatTimer);
    inboxWsHeartbeatTimer = null;
  }
  if (inboxWs) {
    inboxWs.onopen = null;
    inboxWs.onmessage = null;
    inboxWs.onerror = null;
    inboxWs.onclose = null;
    try {
      inboxWs.close();
    } catch {
      // noop
    }
    inboxWs = null;
  }
};

const connectInboxWs = () => {
  const url = buildInboxWsUrl();
  if (!url || !inboxEnabled.value || !inboxFloatingEnabled.value) return;
  const myToken = ++inboxWsToken;
  inboxWsIntentionalClose = false;
  inboxNotifBootAt.value = Date.now();
  if (inboxWsReconnectTimer) {
    clearTimeout(inboxWsReconnectTimer);
    inboxWsReconnectTimer = null;
  }
  if (inboxWsHeartbeatTimer) {
    clearInterval(inboxWsHeartbeatTimer);
    inboxWsHeartbeatTimer = null;
  }
  if (inboxWs) {
    try {
      inboxWs.close();
    } catch {
      // noop
    }
    inboxWs = null;
  }
  const socket = new WebSocket(url);
  inboxWs = socket;
  socket.onopen = () => {
    if (myToken !== inboxWsToken) return;
    inboxWsHeartbeatTimer = setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        try {
          socket.send("ping");
        } catch {
          // noop
        }
      }
    }, 20000);
  };
  socket.onmessage = async evt => {
    if (myToken !== inboxWsToken) return;
    let payload: any = null;
    try {
      payload = JSON.parse(evt.data);
    } catch {
      return;
    }
    if (payload?.type === "whatsapp.message.created" && payload?.message?.direction === "inbound") {
      const messageId = String(payload?.message?.id || payload?.message?.externalMessageId || "");
      if (messageId && notifiedInboundMessageIds.value.includes(messageId)) return;
      const rawTs = payload?.message?.createdAt || payload?.message?.sentAt || payload?.message?.receivedAt || null;
      const messageTs = rawTs ? new Date(rawTs).getTime() : NaN;
      // Ignora backlog antigo que o socket pode reenviar ao conectar.
      if (Number.isFinite(messageTs) && messageTs < inboxNotifBootAt.value - 60_000) return;
      if (messageId) {
        notifiedInboundMessageIds.value = [...notifiedInboundMessageIds.value.slice(-399), messageId];
      }
      const conversationId = Number(payload?.conversation_id || payload?.message?.conversationId || 0);
      if (!conversationId || !agencyStore.currentAgencyId) return;
      try {
        const rows = await listWhatsAppConversations(agencyStore.currentAgencyId);
        const conversation = rows.find(item => item.id === conversationId);
        if (conversation) showFloatingInboxNotification(conversation);
      } catch (err) {
        console.error(err);
      }
    }
  };
  socket.onerror = () => {
    if (myToken !== inboxWsToken) return;
  };
  socket.onclose = event => {
    if (myToken !== inboxWsToken) return;
    if (inboxWsHeartbeatTimer) {
      clearInterval(inboxWsHeartbeatTimer);
      inboxWsHeartbeatTimer = null;
    }
    inboxWs = null;
    if (inboxWsIntentionalClose) return;
    if (event.code === 1008 || event.code === 1011) {
      return;
    }
    inboxWsReconnectTimer = setTimeout(() => {
      if (myToken !== inboxWsToken) return;
      connectInboxWs();
    }, 2500);
  };
};

const adminNavigation = computed<AdminNavItem[]>(() => {
  const items: AdminNavItem[] = [
    { id: "dashboard", type: "link", label: navLabel("dashboard"), to: "/admin/dashboard", iconPath: "/admin/dashboard" },
    { id: "pages", type: "link", label: navLabel("pages"), to: "/admin/pages", iconPath: "/admin/pages" },
    {
      id: "leads",
      type: "group",
      label: t({ pt: "Capta\u00E7\u00E3o de leads", es: "Captacion" }),
      basePath: "/admin/leads",
      iconPath: "/admin/leads",
      children: [
        { label: t({ pt: "Oportunidades", es: "Oportunidades" }), path: "/admin/leads/opportunities" },
        { label: t({ pt: "Formul\u00E1rios", es: "Formularios" }), path: "/admin/leads/forms" },
        { label: navLabel("clients"), path: "/admin/leads/clients" },
        { label: t({ pt: "Configura\u00E7\u00F5es", es: "Configuraciones" }), path: "/admin/leads/settings" }
      ]
    },
    {
      id: "integrations",
      type: "group",
      label: navLabel("integrations"),
      basePath: "/admin/integracoes",
      iconPath: "/admin/integracoes",
      children: [
        { label: t({ pt: "Visão geral", es: "Visión general" }), path: "/admin/integracoes" },
        { label: navLabel("tracking"), path: "/admin/integracoes/rastreamento" },
        { label: "Viaje On", path: "/admin/integracoes/viajeon" },
        { label: "ViajeChat", path: "/admin/integracoes/viajechat" },
        { label: "WhatsApp", path: "/admin/integracoes/atendimento" }
      ]
    },
    {
      id: "agency",
      type: "group",
      label: navLabel("agency"),
      basePath: "/admin/agency",
      iconPath: "/admin/agency",
      children: [
        { label: "Dados da agência", path: "/admin/agency" },
        { label: "Faturas", path: "/admin/agency/invoices" },
        { label: "Equipe", path: "/admin/agency/team" }
      ]
    },
    { id: "lessons", type: "link", label: navLabel("lessons"), to: "/admin/aulas", iconPath: "/admin/aulas" },
    { id: "help", type: "link", label: t({ pt: "Central de Ajuda", es: "Centro de ayuda" }), to: "/admin/ajuda", iconPath: "/admin/ajuda", activeBase: "/admin/ajuda" }
  ];
  if (canAccessCustomDomains.value) {
    items.splice(5, 0, { id: "domains", type: "link", label: navLabel("domains"), to: "/admin/domains", iconPath: "/admin/domains" });
  }
  if (auth.user?.is_superuser) {
    items.push({
      id: "admin-master",
      type: "link",
      label: navLabel("adminMaster"),
      to: "/admin/administracao/dashboard",
      iconPath: "/admin/administracao"
    });
  }
  const filtered = items.filter(item => {
    if (item.id === "dashboard") return hasPermission("dashboard");
    if (item.id === "pages") return hasPermission("pages");
    if (item.id === "leads") return hasPermission("leads");
    if (item.id === "inbox") return hasPermission("leads") && inboxEnabled.value && hasWhatsAppPlanAccess.value;
    if (item.id === "integrations") return hasPermission("integrations");
    if (item.id === "agency") return hasPermission("settings") || (canManageTeam.value && hasPermission("team_management"));
    // Aulas desativadas para as agências (fica a Central de Ajuda); o superadmin continua vendo.
    if (item.id === "lessons") return !!auth.user?.is_superuser;
    return true;
  });
  return filtered
    .map(item => {
      if (item.type !== "group") return item;
      if (item.id === "leads") {
        return {
          ...item,
          children: item.children.filter(child => {
            if (child.path === "/admin/leads/forms") return hasPermission("leads_forms") || hasPermission("leads_full");
            if (child.path === "/admin/leads/opportunities") return hasPermission("leads_opportunities") || hasPermission("leads_full");
            if (child.path === "/admin/leads/clients") return hasPermission("leads_clients") || hasPermission("leads_full");
            if (child.path === "/admin/leads/settings") return hasPermission("leads_settings") || hasPermission("leads_full");
            return hasPermission("leads");
          })
        };
      }
      if (item.id === "integrations") {
        return {
          ...item,
          children: item.children.filter(child => {
            if (child.path === "/admin/integracoes/atendimento") {
              return hasWhatsAppPlanAccess.value;
            }
            return true;
          })
        };
      }
      if (item.id !== "agency") return item;
      return {
        ...item,
        children: item.children.filter(child => {
          if (child.path === "/admin/agency/team") return canManageTeam.value && hasPermission("team_management");
          return hasPermission("settings");
        })
      };
    })
    .filter(item => item.type !== "group" || item.children.length > 0)
    // Sem submenus: cada área abre na primeira aba permitida e troca de aba dentro da própria página.
    .map(item =>
      item.type === "group"
        ? ({ id: item.id, type: "link", label: item.label, to: item.children[0].path, iconPath: item.iconPath, activeBase: item.basePath } as AdminNavLinkItem)
        : item
    );
});

const sidebarSections = computed<SidebarSection[]>(() => {
  const items = adminNavigation.value;
  const byId = new Map(items.map(item => [item.id, item]));
  const sectionsBase: Array<Omit<SidebarSection, "items">> = [
    {
      id: "principal",
      label: t({ pt: "Principal", es: "Principal" }),
      itemIds: ["dashboard", "pages", "leads", "inbox"]
    },
    {
      id: "configurar",
      label: t({ pt: "Configurar", es: "Configurar" }),
      itemIds: ["integrations", "agency", "domains", "profile"]
    },
    {
      id: "aprender",
      label: t({ pt: "Aprender", es: "Aprender" }),
      itemIds: ["help", "lessons"]
    },
    {
      id: "plataforma",
      label: t({ pt: "Plataforma", es: "Plataforma" }),
      itemIds: ["admin-master"]
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

const isPathActive = (path: string) => {
  if (path === "/admin/agency" || path === "/admin/integracoes") {
    return route.path === path;
  }
  return route.path === path || route.path.startsWith(`${path}/`);
};

const isChildActive = (path: string) => isPathActive(path);

const isTopLevelActive = (item: AdminNavLinkItem) => {
  if (item.id === "admin-master") return isPathActive("/admin/administracao");
  if (item.activeBase) return route.path === item.activeBase || route.path.startsWith(`${item.activeBase}/`);
  return isPathActive(item.to);
};

const isParentActive = (item: AdminNavGroupItem) =>
  route.path === item.basePath || route.path.startsWith(`${item.basePath}/`);

const isGroupExpanded = (item: AdminNavGroupItem) => Boolean(navGroupExpandedState.value[item.id]);

const toggleNavGroup = (groupId: string) => {
  const currentlyOpen = Boolean(navGroupExpandedState.value[groupId]);
  const next: Record<string, boolean> = {};
  if (!currentlyOpen) {
    next[groupId] = true;
  }
  navGroupExpandedState.value = next;
};

// Ao navegar, abre o grupo da página atual e fecha os outros (mesmo se o grupo
// tinha sido fechado antes), para o item ativo nunca ficar escondido.
const ensureActiveGroupDefaultOpen = () => {
  for (const item of adminNavigation.value) {
    if (item.type !== "group") continue;
    if (!isParentActive(item)) continue;
    navGroupExpandedState.value = { [item.id]: true };
    return;
  }
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

watch(
  () => route.path,
  () => {
    ensureActiveGroupDefaultOpen();
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


const agencyName = computed(() => agencyStore.currentAgency?.name || agencyStore.agencies[0]?.name || "");
const sidebarLogoSrc = SidebarLogo;
const mobileHeaderLogoSrc = computed(() => (isDarkTheme.value ? sidebarLogoSrc : ColoredLogo));

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

const handlePermissionDeniedToast = (event: Event) => {
  const customEvent = event as CustomEvent<{ message?: string }>;
  const message = customEvent.detail?.message || "Seu perfil não tem permissão para executar esta ação.";
  permissionSnackbar.value = { open: true, message };
  if (permissionSnackbarTimer) window.clearTimeout(permissionSnackbarTimer);
  permissionSnackbarTimer = window.setTimeout(() => {
    permissionSnackbar.value.open = false;
  }, 3500);
};

const handleLogout = async () => {
  await auth.logout();
  router.push({ name: "login" });
};

const showWelcomeDialog = ref(false);
const showEndDialog = ref(false);
const showSubscriptionBlockedDialog = ref(false);
const showTrialWarning3Days = ref(false);
const showTrialWarning1Day = ref(false);
const mobileMenuOpen = ref(false);

// Sidebar recolhível (só ícones), como no Viaje On. A preferência fica no navegador.
const SIDEBAR_COLLAPSED_KEY = "admin_sidebar_collapsed";
const readSidebarCollapsed = () => {
  try {
    return typeof window !== "undefined" && window.localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
};
const sidebarCollapsed = ref(readSidebarCollapsed());
const flyoutGroupId = ref<string | null>(null);
const brandMarkSrc = BrandMark;
const canCreatePageShortcut = computed(() => hasPermission("pages"));
// Solto (não fixado), o menu fica só com ícones e abre ao passar o mouse, empurrando a página.
// No Admin Master o menu principal fica sempre recolhido, para caber o menu do Admin (como no Viaje On).
const sidebarPeek = ref(false);
const sidebarCompact = computed(() => isAdminMasterRoute.value || (sidebarCollapsed.value && !sidebarPeek.value));
// Mesmas medidas do Viaje On: cartão de 244px (64px recolhido), solto 12px da borda.
const sidebarOffset = computed(() => (sidebarCompact.value ? "88px" : "256px"));
let sidebarPeekTimer: ReturnType<typeof setTimeout> | null = null;
const peekSidebar = (open: boolean) => {
  if (sidebarPeekTimer) clearTimeout(sidebarPeekTimer);
  if (isAdminMasterRoute.value) {
    sidebarPeek.value = false;
    return;
  }
  // Abre depois de uma pausa curta e fecha com um pequeno atraso, para não piscar ao passar de relance.
  sidebarPeekTimer = setTimeout(() => {
    sidebarPeek.value = open;
    if (open) {
      flyoutGroupId.value = null;
      hideSidebarTip();
    }
  }, open ? 120 : 180);
};
const handleSidebarFocusOut = (event: FocusEvent) => {
  const next = event.relatedTarget as Node | null;
  if (!next || !(event.currentTarget as HTMLElement).contains(next)) peekSidebar(false);
};

const toggleSidebarCollapsed = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
  flyoutGroupId.value = null;
  try {
    window.localStorage.setItem(SIDEBAR_COLLAPSED_KEY, sidebarCollapsed.value ? "1" : "0");
  } catch {
    // Sem acesso ao armazenamento: a escolha vale só nesta aba.
  }
};

// Submenu e dicas da barra recolhida ficam fora da área com rolagem (Teleport),
// presos à posição do ícone; dentro dela eram cortados ou invadiam o rodapé.
const flyoutTop = ref(0);
const flyoutLeft = ref(0);
const sidebarTip = ref<{ text: string; top: number; left: number }>({ text: "", top: 0, left: 0 });
const SIDEBAR_POPOVER_GAP = 14;

const sidebarEdge = () => {
  const panel = document.querySelector(".admin-sidebar .as-panel");
  return panel ? panel.getBoundingClientRect().right : 0;
};

const placeFlyout = (anchor: HTMLElement) => {
  const rect = anchor.getBoundingClientRect();
  flyoutLeft.value = sidebarEdge() + SIDEBAR_POPOVER_GAP;
  flyoutTop.value = rect.top - 6;
  void nextTick(() => {
    const height = document.querySelector(".as-flyout")?.getBoundingClientRect().height ?? 0;
    const maxTop = window.innerHeight - height - 12;
    flyoutTop.value = Math.max(12, Math.min(flyoutTop.value, maxTop));
  });
};

const handleGroupClick = (groupId: string, event?: MouseEvent) => {
  if (sidebarCompact.value) {
    const opening = flyoutGroupId.value !== groupId;
    flyoutGroupId.value = opening ? groupId : null;
    sidebarTip.value = { text: "", top: 0, left: 0 };
    if (opening && event?.currentTarget instanceof HTMLElement) placeFlyout(event.currentTarget);
    return;
  }
  toggleNavGroup(groupId);
};

const closeSidebarFlyout = () => {
  flyoutGroupId.value = null;
};

const showSidebarTip = (event: Event) => {
  if (!sidebarCompact.value) return;
  const target = (event.target as HTMLElement | null)?.closest<HTMLElement>("[data-tip]");
  const text = target?.dataset.tip;
  if (!target || !text) {
    sidebarTip.value = { text: "", top: 0, left: 0 };
    return;
  }
  const rect = target.getBoundingClientRect();
  sidebarTip.value = { text, top: rect.top + rect.height / 2, left: sidebarEdge() + SIDEBAR_POPOVER_GAP };
};

const hideSidebarTip = () => {
  sidebarTip.value = { text: "", top: 0, left: 0 };
};

const handleSidebarKeydown = (event: KeyboardEvent) => {
  if (event.key === "Escape") closeSidebarFlyout();
};

watch(
  sidebarOffset,
  value => {
    if (typeof document === "undefined") return;
    document.documentElement.style.setProperty("--admin-sidebar-offset", value);
  },
  { immediate: true }
);

watch(
  () => route.fullPath,
  () => {
    flyoutGroupId.value = null;
    hideSidebarTip();
  }
);

onMounted(() => {
  document.addEventListener("click", closeSidebarFlyout);
  document.addEventListener("keydown", handleSidebarKeydown);
  window.addEventListener("resize", closeSidebarFlyout);
});
// Liga o fundo âmbar do Admin Master (fica no body, atrás de todo o painel).
watch(
  isAdminMasterRoute,
  active => {
    if (typeof document === "undefined") return;
    document.body.classList.toggle("admin-master-active", active);
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  document.removeEventListener("click", closeSidebarFlyout);
  document.removeEventListener("keydown", handleSidebarKeydown);
  window.removeEventListener("resize", closeSidebarFlyout);
  document.body.classList.remove("admin-master-active");
});
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
  () => [trialBlocked.value, route.fullPath],
  () => {
    if (trialBlocked.value) {
      showEndDialog.value = route.path !== "/admin/planos";
    } else {
      showEndDialog.value = false;
    }
  },
  { immediate: true }
);

watch(
  () => [subscriptionBlocked.value, route.path, auth.user?.id],
  () => {
    showSubscriptionBlockedDialog.value = Boolean(subscriptionBlocked.value && route.path !== "/admin/planos");
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

const goToPlansFromSubscriptionBlock = () => {
  goToPlans();
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

const AGENCY_SLUG_MAX_LENGTH = 30;

const buildAgencySlugCandidate = (name: string, attempt = 0) => {
  const baseSlug = normalizeAgencySlugInput(name, AGENCY_SLUG_MAX_LENGTH) || "agencia";
  const suffix = attempt === 0 ? "" : `-${attempt}`;
  const availableLength = Math.max(1, AGENCY_SLUG_MAX_LENGTH - suffix.length);
  const trimmedBase = baseSlug.slice(0, availableLength).replace(/^-+|-+$/g, "");
  return `${trimmedBase || "agencia"}${suffix}`.slice(0, AGENCY_SLUG_MAX_LENGTH).replace(/^-+|-+$/g, "");
};

const createAgencyWithSlugFallback = async (payload: AgencyPayload) => {
  const baseSlug = buildAgencySlugCandidate(payload.name);
  const maxAttempts = 8;
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const slugCandidate = buildAgencySlugCandidate(baseSlug, attempt);
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
  await api.put(`/agencies/${targetId}`, payload);
  await agencyStore.loadAgencies();
  ensureAgencySelection(targetId);
  return targetId;
};

const startAgencySetupFlow = async () => {
  await acknowledgeTrial("start");
  resetAgencySetupForm();
  showAgencySetupFlow.value = true;
};

const openAgencySetupFlow = () => {
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
      await api.put(`/agencies/${agencyId}`, payload);
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

const loadViajeonConnection = async () => {
  try {
    const response = await api.get("/integrations/viajeon");
    viajeonConnected.value = response.data?.connected === true;
    viajeonSsoEmail.value = String(response.data?.sso_email || "");
  } catch {
    viajeonConnected.value = false;
    viajeonSsoEmail.value = "";
  }
};

watch(
  () => agencyStore.currentAgencyId,
  () => {
    if (auth.user?.id) void loadViajeonConnection();
  }
);

const openViajeonPanel = async () => {
  if (viajeonSsoLoading.value) return;
  viajeonSsoLoading.value = true;
  try {
    const response = await api.post<{ url: string }>("/integrations/viajeon/sso");
    window.location.href = response.data.url;
  } catch (err) {
    const message = (err as any)?.response?.data?.detail || "Não foi possível gerar o login agora. Tente novamente.";
    permissionSnackbar.value = { open: true, message };
    if (permissionSnackbarTimer) window.clearTimeout(permissionSnackbarTimer);
    permissionSnackbarTimer = window.setTimeout(() => {
      permissionSnackbar.value.open = false;
    }, 5000);
    if ((err as any)?.response?.status === 401 || (err as any)?.response?.status === 409) {
      viajeonConnected.value = false;
      viajeonSsoEmail.value = "";
    }
  } finally {
    viajeonSsoLoading.value = false;
  }
};

onMounted(async () => {
  themeStore.activateDocumentTheme();
  window.addEventListener(API_PERMISSION_DENIED_EVENT, handlePermissionDeniedToast as EventListener);
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
  await loadViajeonConnection();
  const shouldForceOnboarding = String(route.query.onboarding || "") === "1";
  if (shouldForceOnboarding) {
    openAgencySetupFlow();
    const nextQuery = { ...route.query } as Record<string, unknown>;
    delete nextQuery.onboarding;
    router.replace({ path: route.path, query: nextQuery }).catch(() => {});
  }
  await loadInboxAccess();
  void pollInboxFloatingNotifications();
  connectInboxWs();
  inboxFloatingPollTimer = setInterval(() => {
    if (!inboxWs) void pollInboxFloatingNotifications();
  }, 8000);
  checkCookieConsent();
  scrollToTop();
});

onBeforeUnmount(() => {
  themeStore.deactivateDocumentTheme();
  window.removeEventListener(API_PERMISSION_DENIED_EVENT, handlePermissionDeniedToast as EventListener);
  if (permissionSnackbarTimer) {
    window.clearTimeout(permissionSnackbarTimer);
  }
  if (removeViewportWatcher) {
    removeViewportWatcher();
  }
  if (hasWindow) {
    document.body.classList.remove(bodyDarkClass, bodyLightClass);
  }
  if (inboxFloatingPollTimer) {
    clearInterval(inboxFloatingPollTimer);
    inboxFloatingPollTimer = null;
  }
  disconnectInboxWs();
  if (inboxWsReconnectTimer) {
    clearTimeout(inboxWsReconnectTimer);
    inboxWsReconnectTimer = null;
  }
  if (inboxFloatingHideTimer) {
    clearTimeout(inboxFloatingHideTimer);
    inboxFloatingHideTimer = null;
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

watch(
  () => [auth.user?.id, agencyStore.currentAgencyId],
  () => {
    loadInboxAccess();
    lastInboxSnapshot.value = {};
    notifiedInboundMessageIds.value = [];
    inboxNotifBootAt.value = Date.now();
    void pollInboxFloatingNotifications();
    disconnectInboxWs();
    connectInboxWs();
  },
  { immediate: true }
);

watch(
  () => [inboxEnabled.value, inboxFloatingEnabled.value],
  () => {
    if (!inboxEnabled.value || !inboxFloatingEnabled.value) {
      disconnectInboxWs();
      return;
    }
    connectInboxWs();
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
   ROOT / FUNDO GLOBAL
========================= */

html,
body,
#app {
  min-height: 100%;
}

body.admin-body-dark,
body.admin-body-dark #app {
  background-color: var(--background);
  background-image: none;
}

body.admin-body-light,
body.admin-body-light #app {
  background-color: var(--background);
  background-image: none;
}


/* =========================
   THEMES
========================= */

.light-theme {
  background: var(--background);
  color: var(--foreground);
}

.dark-theme {
  background: var(--background);
  color: var(--foreground);
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

/* Admin master: o menu principal fica recolhido e o menu do Admin entra ao lado,
   como um cartão solto da borda (mesmo desenho do Viaje On). */
@media (min-width: 1180px) {
  .admin-master-rail {
    position: fixed;
    top: 12px;
    bottom: 12px;
    left: var(--admin-sidebar-offset, 88px);
    z-index: 20;
    width: 232px;
    transition: left 200ms ease-out;
  }
  .admin-master-main {
    margin-left: 244px;
  }
}

/* O fundo âmbar do Admin Master fica no body (main.css); as camadas do painel ficam transparentes. */
.admin-shell-root.is-admin-master,
.is-admin-master .admin-main,
.is-admin-master .admin-content,
.is-admin-master .admin-content > div {
  background: transparent !important;
}
@media (max-width: 1179px) {
  .admin-master-rail {
    margin-bottom: 16px;
  }
}


/* =========================
   DARK MODE OVERRIDES
========================= */

.dark-theme .admin-main {
  background: var(--background);
  color: var(--foreground);
}

.dark-theme .admin-content {
  color: var(--foreground);
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
  transition: opacity 200ms ease-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.mobile-sidebar-enter-active {
  transition: opacity 300ms ease-out;
}

.mobile-sidebar-leave-active {
  transition: opacity 200ms ease-out;
}

.mobile-sidebar-enter-active .mobile-menu-panel {
  transition: transform 300ms ease-out;
}

.mobile-sidebar-leave-active .mobile-menu-panel {
  transition: transform 200ms ease-out;
}

.mobile-sidebar-enter-from,
.mobile-sidebar-leave-to {
  opacity: 0;
}

.mobile-sidebar-enter-from .mobile-menu-panel,
.mobile-sidebar-leave-to .mobile-menu-panel {
  transform: translateX(calc(100% + 12px));
}

/* Celular: cabeçalho em cartão preso no topo. A faixa atrás dele tem o fundo da página,
   para o conteúdo que rola não aparecer em volta do cartão. */
.mobile-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  flex-shrink: 0;
  padding: 12px 12px 6px;
  background: linear-gradient(to bottom, var(--background) calc(100% - 6px), transparent);
}

.mobile-topbar-card {
  display: flex;
  height: 64px;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 12px 0 16px;
  border-radius: 20px;
  background: var(--card);
  box-shadow: var(--shadow-card);
}

/* Menu do celular: cartão solto da borda, com o mesmo conteúdo do menu do computador.
   O escurecido cobre a tela toda, inclusive em volta do cartão. */
.mobile-menu-overlay {
  position: absolute;
  inset: 0;
  background: rgba(9, 17, 13, 0.42);
  backdrop-filter: blur(2px);
}

.mobile-menu-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 18rem;
  max-width: calc(100vw - 24px);
  height: calc(100% - 24px);
  height: calc(100dvh - 24px);
  margin: 12px;
  padding: 16px 12px 12px;
  border-radius: 20px;
  background: var(--sidebar);
  color: var(--sidebar-foreground);
  box-shadow: var(--shadow-elegant);
}

.mobile-menu-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-left: 4px;
}

.mobile-menu-close {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--muted) 80%, transparent);
  color: var(--muted-foreground);
  transition: background-color 200ms ease-out, color 200ms ease-out;
}

.mobile-menu-close:hover {
  background: var(--muted);
  color: var(--foreground);
}

.mobile-menu-close svg {
  width: 16px;
  height: 16px;
}

@media (prefers-reduced-motion: reduce) {
  .mobile-sidebar-enter-active,
  .mobile-sidebar-leave-active,
  .mobile-sidebar-enter-active .mobile-menu-panel,
  .mobile-sidebar-leave-active .mobile-menu-panel {
    transition: none;
  }
}

.nav-pill-badge {
  margin-left: auto;
  background: var(--muted);
  color: var(--foreground);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 999px;
  line-height: 1;
}

.nav-master-badge {
  margin-left: auto;
  border-radius: 999px;
  background: var(--status-warning);
  color: var(--status-warning-foreground);
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.04em;
  line-height: 1;
}

.is-active .nav-pill-badge {
  background: var(--card);
  color: var(--accent-foreground);
}

.sidebar-scroll {
  scrollbar-width: thin;
  scrollbar-color: var(--sidebar-border) transparent;
}

.sidebar-scroll::-webkit-scrollbar {
  width: 6px;
}

.sidebar-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-scroll::-webkit-scrollbar-thumb {
  background: var(--sidebar-border);
  border-radius: 999px;
}

.sidebar-scroll::-webkit-scrollbar-thumb:hover {
  background: var(--muted-foreground);
}

/* =========================
   SIDEBAR (mesmo desenho do Viaje On)
   Cartão de 244px solto 12px da borda (64px recolhido), cantos de 20px,
   itens de 40px com texto de 14px e ícones de 16px. Abre e fecha em 200ms.
========================= */

@media (min-width: 768px) {
  .admin-main {
    margin-left: var(--admin-sidebar-offset, 256px);
    transition: margin-left 200ms ease-out;
  }
}

.admin-sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  z-index: 30;
  width: 256px;
  padding: 12px 0 12px 12px;
  transition: width 200ms ease-out;
}

.admin-sidebar.is-collapsed {
  width: 76px;
}

.as-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  padding: 16px 12px 12px;
  border-radius: 20px;
  background: var(--sidebar);
  color: var(--sidebar-foreground);
  box-shadow: var(--shadow-card);
}

.as-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  margin-bottom: 12px;
}

.as-brand-logo {
  display: flex;
  min-width: 0;
  align-items: center;
  padding: 0 4px;
}

/* O PNG do logo tem faixas vazias em cima e embaixo: o recorte mostra só o desenho. */
.as-logo-img {
  width: 120px;
  height: 36px;
  object-fit: cover;
}

.as-brand-tile {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
}

.as-pin {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  margin-left: auto;
  flex-shrink: 0;
  border-radius: 999px;
  color: var(--muted-foreground);
  transition: background-color 200ms ease-out, color 200ms ease-out;
}

.as-pin:hover {
  background: var(--sidebar-accent);
  color: var(--foreground);
}

.as-pin svg {
  width: 16px;
  height: 16px;
}

.as-pin.is-pinned {
  color: var(--primary);
}

.as-pin.is-pinned svg {
  fill: currentColor !important;
}

.as-cta {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 40px;
  margin: 0 0 12px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--primary);
  color: var(--primary-foreground);
  font-size: 14px;
  font-weight: 600;
  transition: background-color 200ms ease-out, filter 200ms ease-out;
}

.as-cta:hover {
  filter: brightness(1.08);
}

.as-cta-icon {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.as-cta-icon svg {
  width: 16px;
  height: 16px;
}

.as-nav {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.as-section {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.as-section-title {
  display: flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  color: color-mix(in srgb, var(--sidebar-foreground) 60%, transparent);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  white-space: nowrap;
}

.as-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-height: 40px;
  padding: 0 12px;
  border-radius: 999px;
  color: var(--sidebar-foreground);
  font-size: 14px;
  font-weight: 400;
  text-align: left;
  transition: background-color 200ms ease-out, color 200ms ease-out;
}

.as-icon {
  display: grid;
  place-items: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.as-icon svg {
  width: 16px;
  height: 16px;
}

.as-item:hover {
  background: var(--sidebar-accent);
  color: var(--foreground);
}

.as-item.is-active,
.as-item.is-active:hover {
  background: var(--accent);
  color: var(--accent-foreground);
  font-weight: 600;
}

.as-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.as-chevron {
  width: 16px;
  height: 16px;
  margin-left: auto;
  color: var(--muted-foreground);
  transition: transform 200ms ease-out;
}

.as-group {
  position: relative;
}

.as-children {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 2px 0 6px 19px;
  padding-left: 12px;
  border-left: 1px solid var(--sidebar-border);
}

.as-child {
  display: block;
  padding: 8px 12px;
  border-radius: 999px;
  color: var(--muted-foreground);
  font-size: 13px;
  font-weight: 500;
  transition: background-color 200ms ease-out, color 200ms ease-out;
}

.as-child:hover {
  background: var(--sidebar-accent);
  color: var(--foreground);
}

.as-child.is-active {
  background: var(--accent);
  color: var(--accent-foreground);
  font-weight: 600;
}

.as-flyout {
  position: fixed;
  z-index: 70;
  min-width: 224px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--popover);
  color: var(--popover-foreground);
  box-shadow: var(--shadow-elegant);
}

.as-flyout-title {
  padding: 6px 12px 8px;
  color: var(--muted-foreground);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.as-flyout-enter-active,
.as-flyout-leave-active {
  transition: opacity 200ms ease-out, transform 200ms ease-out;
}

.as-flyout-enter-from,
.as-flyout-leave-to {
  opacity: 0;
  transform: translateX(-4px);
}

.as-footer {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 8px;
}

.as-switch {
  position: relative;
  width: 36px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--input);
  transition: background-color 200ms ease-out;
}

.as-switch span {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  border-radius: 999px;
  background: #fff;
  box-shadow: var(--shadow-soft);
  transition: transform 200ms ease-out;
}

.as-switch.on {
  background: var(--primary);
}

.as-switch.on span {
  transform: translateX(16px);
}

.as-user {
  display: flex;
  align-items: center;
  gap: 4px;
}

.as-user-link {
  position: relative;
  display: flex;
  flex: 1;
  align-items: center;
  gap: 10px;
  min-width: 0;
  min-height: 44px;
  padding: 0 4px;
  border-radius: 999px;
  transition: background-color 200ms ease-out;
}

.as-user-link:hover {
  background: var(--sidebar-accent);
}

.as-avatar {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 999px;
  background: var(--accent);
  color: var(--accent-foreground);
  font-size: 12px;
  font-weight: 600;
}

.as-logout {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 999px;
  color: var(--muted-foreground);
  transition: background-color 200ms ease-out, color 200ms ease-out;
}

.as-logout:hover {
  background: var(--sidebar-accent);
  color: var(--foreground);
}

.as-logout svg {
  width: 16px;
  height: 16px;
}

/* Solto: os textos aparecem junto com a abertura do menu. */
.admin-sidebar.is-peek .as-label,
.admin-sidebar.is-peek .as-section-title {
  animation: as-label-in 200ms ease-out both;
}
@keyframes as-label-in {
  from { opacity: 0; }
}
@media (prefers-reduced-motion: reduce) {
  .admin-sidebar,
  .admin-main { transition: none; }
  .admin-sidebar.is-peek .as-label,
  .admin-sidebar.is-peek .as-section-title { animation: none; }
}

/* Recolhido: botões redondos de 40px, centralizados na coluna. */
.admin-sidebar.is-collapsed .as-panel {
  overflow: hidden;
}

.admin-sidebar.is-collapsed .as-brand {
  flex-direction: column;
  justify-content: center;
}

.admin-sidebar.is-collapsed .as-brand-tile {
  width: 40px;
  height: 40px;
}

/* Com mouse, o menu recolhido abre ao passar por cima; o alfinete aparece aberto.
   Na tela de toque ele fica embaixo do logo. */
@media (hover: hover) {
  .admin-sidebar.is-collapsed .as-pin {
    display: none;
  }
}
.admin-sidebar.is-collapsed .as-pin {
  margin-left: 0;
}

.admin-sidebar.is-collapsed .as-label,
.admin-sidebar.is-collapsed .as-chevron,
.admin-sidebar.is-collapsed .as-switch {
  display: none;
}

/* O título da seção vira um traço na mesma altura do título: os itens ficam
   na mesma posição com o menu aberto ou recolhido. */
.admin-sidebar.is-collapsed .as-section-title {
  position: relative;
  justify-content: center;
  width: 40px;
  padding: 0;
  overflow: hidden;
  color: transparent;
}

.admin-sidebar.is-collapsed .as-section-title::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 8px;
  right: 8px;
  height: 1px;
  background: color-mix(in srgb, var(--sidebar-foreground) 22%, transparent);
}

.admin-sidebar.is-collapsed .as-cta,
.admin-sidebar.is-collapsed .as-item {
  justify-content: center;
  width: 40px;
  padding: 0;
}

.admin-sidebar.is-collapsed .as-nav {
  scrollbar-width: none;
}

.admin-sidebar.is-collapsed .as-nav::-webkit-scrollbar {
  display: none;
}

.admin-sidebar.is-collapsed .as-item.is-open {
  background: var(--sidebar-accent);
}

.admin-sidebar.is-collapsed .as-user-link {
  flex: none;
  justify-content: center;
  width: 40px;
  padding: 0;
}

/* Telas baixas: itens mais compactos para caber sem rolar (mesmas faixas do Viaje On). */
@media (max-height: 820px) {
  .as-item,
  .as-cta,
  .as-user-link {
    min-height: 36px;
    height: auto;
  }
  .as-cta {
    height: 36px;
  }
  .as-brand {
    margin-bottom: 8px;
  }
  .as-section-title {
    height: 28px;
  }
  .admin-sidebar.is-collapsed .as-cta,
  .admin-sidebar.is-collapsed .as-item {
    width: 36px;
    height: 36px;
    min-height: 36px;
  }
}
@media (max-height: 680px) {
  .as-item,
  .as-cta {
    min-height: 32px;
  }
  /* Nome e cargo ocupam 36px: o recolhido usa a mesma altura para não mexer o rodapé. */
  .as-user-link {
    min-height: 36px;
  }
  .as-cta {
    height: 32px;
  }
  .as-section-title {
    height: 24px;
  }
  .as-nav {
    gap: 4px;
  }
  .admin-sidebar.is-collapsed .as-cta,
  .admin-sidebar.is-collapsed .as-item {
    width: 32px;
    height: 32px;
    min-height: 32px;
  }
}

.as-tip {
  position: fixed;
  z-index: 80;
  padding: 6px 10px;
  border-radius: 10px;
  background: var(--foreground);
  color: var(--background);
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  pointer-events: none;
  transform: translateY(-50%);
}
</style>


















