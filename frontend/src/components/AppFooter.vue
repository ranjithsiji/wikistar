<template>
  <footer class="border-t border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 mt-12">
    <div class="max-w-6xl mx-auto px-4 py-5 flex flex-wrap items-center gap-x-5 gap-y-2
                text-sm text-neutral-500 dark:text-neutral-400">
      <span class="font-semibold text-neutral-700 dark:text-neutral-300">
        Wiki<span class="text-blue-600 dark:text-blue-400">STAR</span>
      </span>
      <router-link to="/about" class="hover:text-neutral-900 dark:hover:text-neutral-100">
        About
      </router-link>
      <a href="https://gitlab.wikimedia.org/toolforge-repos/wikistar"
         target="_blank" rel="noopener"
         class="hover:text-neutral-900 dark:hover:text-neutral-100">Source code</a>
      <a href="https://gitlab.wikimedia.org/toolforge-repos/wikistar/-/issues"
         target="_blank" rel="noopener"
         class="hover:text-neutral-900 dark:hover:text-neutral-100">Report an issue</a>
      <a href="https://www.gnu.org/licenses/gpl-3.0.html"
         target="_blank" rel="noopener"
         class="hover:text-neutral-900 dark:hover:text-neutral-100">GPL-3.0</a>
      <span class="flex-1"></span>
      <span>
        Hosted on
        <a href="https://toolforge.org" target="_blank" rel="noopener"
           class="underline decoration-dotted hover:text-neutral-900 dark:hover:text-neutral-100">
          Wikimedia Toolforge</a>
      </span>
    </div>
  </footer>
</template>
