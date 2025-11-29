<template>
  <div>
    <h4>Your Activity Overview</h4>
    <div class="row">
      <div class="col-md-3 mb-3">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title">{{ stats.participated }}</h5>
            <p class="card-text">Editathons Participated</p>
          </div>
        </div>
      </div>
      <div class="col-md-3 mb-3">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title">{{ stats.created }}</h5>
            <p class="card-text">Editathons Created</p>
          </div>
        </div>
      </div>
      <div class="col-md-3 mb-3">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title">{{ stats.articles }}</h5>
            <p class="card-text">Articles Submitted</p>
          </div>
        </div>
      </div>
      <div class="col-md-3 mb-3">
        <div class="card text-center">
          <div class="card-body">
            <h5 class="card-title">{{ stats.points }}</h5>
            <p class="card-text">Total Points</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  user: String,
  stats: Object
})
</script>