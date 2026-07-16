<template>
  <footer class="bg-[#0b1023] text-slate-300 mt-12">
    <div class="max-w-6xl mx-auto px-4 py-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
      <span class="font-semibold text-white">
        Wiki<span class="text-blue-400">STAR</span>
      </span>
      <router-link to="/about" class="hover:text-white">
        About
      </router-link>
      <a href="https://gitlab.wikimedia.org/toolforge-repos/wikistar"
         target="_blank" rel="noopener"
         class="hover:text-white">Source code</a>
      <a href="https://gitlab.wikimedia.org/toolforge-repos/wikistar/-/issues"
         target="_blank" rel="noopener"
         class="hover:text-white">Report an issue</a>
      <a href="https://www.gnu.org/licenses/gpl-3.0.html"
         target="_blank" rel="noopener"
         class="hover:text-white">GPL-3.0</a>
      <span class="flex-1"></span>
      <span>
        Hosted on
        <a href="https://toolforge.org" target="_blank" rel="noopener"
           class="underline decoration-dotted hover:text-white">
          Wikimedia Toolforge</a>
      </span>
    </div>
  </footer>
</template>
