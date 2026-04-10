<template>
  <LuminousFrame title="核心信号塔" eyebrow="Signal Towers" subtitle="用数据显示塔代替普通 KPI 卡片" :accent-start="accentStart" :accent-end="accentEnd">
    <div class="tower-group">
      <DataTower
        v-for="tower in towers"
        :key="tower.label"
        :value="tower.value"
        :label="tower.label"
        :note="tower.note"
        :suffix="tower.suffix"
        :color-a="tower.colorA"
        :color-b="tower.colorB"
      />
    </div>
  </LuminousFrame>
</template>

<script setup>
import DataTower from './DataTower.vue'
import LuminousFrame from './LuminousFrame.vue'

defineOptions({ name: 'DataTowerGroup' })

defineProps({
  towers: {
    type: Array,
    default: () => [],
  },
  accentStart: {
    type: String,
    default: '#ff8f7a',
  },
  accentEnd: {
    type: String,
    default: '#58cbff',
  },
})
</script>

<style scoped>
.tower-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  align-items: end;
}

@media (max-width: 1200px) {
  .tower-group {
    grid-template-columns: 1fr;
    gap: 18px;
  }
}
</style>
