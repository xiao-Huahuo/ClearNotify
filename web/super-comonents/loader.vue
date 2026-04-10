<style scoped>
  .loader {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    right: 0;
  }

  .jimu-primary-loading:before,
  .jimu-primary-loading:after {
    position: absolute;
    top: 0;
    content: '';
  }

  .jimu-primary-loading:before {
    left: -9.996px;
  }

  .jimu-primary-loading:after {
    left: 9.996px;
    -webkit-animation-delay: 0.32s !important;
    animation-delay: 0.32s !important;
  }

  .jimu-primary-loading:before,
  .jimu-primary-loading:after,
  .jimu-primary-loading {
    background: var(--loader-color, #076fe5);
    -webkit-animation: loading-keys-app-loading 0.8s infinite ease-in-out;
    animation: loading-keys-app-loading 0.8s infinite ease-in-out;
    width: 6.8px;
    height: 16px;
  }

  .jimu-primary-loading {
    text-indent: -9999em;
    margin: auto;
    position: absolute;
    right: calc(50% - 3.4px);
    top: calc(50% - 8px);
    -webkit-animation-delay: 0.16s !important;
    animation-delay: 0.16s !important;
  }

  @-webkit-keyframes loading-keys-app-loading {

    0%,
    80%,
    100% {
      opacity: .75;
      box-shadow: 0 0 var(--loader-color, #076fe5);
      height: 16px;
    }

    40% {
      opacity: 1;
      box-shadow: 0 -4px var(--loader-color, #076fe5);
      height: 20px;
    }
  }

  @keyframes loading-keys-app-loading {

    0%,
    80%,
    100% {
      opacity: .75;
      box-shadow: 0 0 var(--loader-color, #076fe5);
      height: 16px;
    }

    40% {
      opacity: 1;
      box-shadow: 0 -4px var(--loader-color, #076fe5);
      height: 20px;
    }
  }
</style>

<template>
  <div class="loader">
    <div class="justify-content-center jimu-primary-loading"></div>
  </div>
</template>
