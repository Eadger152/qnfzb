/* ==========================================================================
   华中师范大学政治与国际关系学院团委 · 青年发展部  站点脚本
   零依赖：日期、移动端导航、返回顶部、常见问题折叠、图片灯箱、滚动显现
   ========================================================================== */
(function () {
  'use strict';

  function ready(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }

  ready(function () {

    /* ---------- 1. 顶部日期 ---------- */
    var dateEl = document.getElementById('today');
    if (dateEl) {
      var d = new Date();
      var weeks = ['日', '一', '二', '三', '四', '五', '六'];
      dateEl.textContent = d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日 · 星期' + weeks[d.getDay()];
    }

    /* ---------- 2. 移动端导航展开 ---------- */
    var nav = document.getElementById('mainnav');
    var toggle = document.getElementById('navToggle');
    if (nav && toggle) {
      toggle.addEventListener('click', function () {
        nav.classList.toggle('open');
        var open = nav.classList.contains('open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.querySelector('.nt-text').textContent = open ? '收起目录' : '网站目录';
      });
      // 点击导航项后自动收起
      Array.prototype.forEach.call(nav.querySelectorAll('a.nav-link'), function (a) {
        a.addEventListener('click', function () { nav.classList.remove('open'); });
      });
    }

    /* ---------- 3. 当前页导航高亮 ---------- */
    (function highlight() {
      if (!nav) { return; }
      var path = window.location.pathname.split('/').pop() || 'index.html';
      var links = nav.querySelectorAll('a.nav-link');
      var matched = false;
      Array.prototype.forEach.call(links, function (a) {
        var href = (a.getAttribute('href') || '').split('#')[0].split('/').pop();
        if (href && href === path) {
          a.classList.add('active');
          matched = true;
        }
      });
      if (!matched && links.length) { links[0].classList.add('active'); }
    })();

    /* ---------- 4. 返回顶部 ---------- */
    var toTop = document.getElementById('toTop');
    if (toTop) {
      var onScroll = function () {
        if (window.pageYOffset > 380) { toTop.classList.add('show'); }
        else { toTop.classList.remove('show'); }
      };
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
      toTop.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    /* ---------- 5. 常见问题折叠 ---------- */
    var faqItems = document.querySelectorAll('.faq-item');
    Array.prototype.forEach.call(faqItems, function (item) {
      var q = item.querySelector('.faq-q');
      if (!q) { return; }
      q.addEventListener('click', function () {
        var isOpen = item.classList.contains('open');
        Array.prototype.forEach.call(faqItems, function (other) {
          other.classList.remove('open');
          var oq = other.querySelector('.faq-q');
          if (oq) { oq.setAttribute('aria-expanded', 'false'); }
        });
        if (!isOpen) {
          item.classList.add('open');
          q.setAttribute('aria-expanded', 'true');
        }
      });
    });

    /* ---------- 6. 图片灯箱 ---------- */
    var box = document.getElementById('lightbox');
    if (box) {
      var boxImg = box.querySelector('img');
      var boxCap = box.querySelector('.cap');

      var openBox = function (src, cap) {
        boxImg.setAttribute('src', src);
        boxCap.textContent = cap || '';
        box.classList.add('open');
        document.body.style.overflow = 'hidden';
      };
      var closeBox = function () {
        box.classList.remove('open');
        boxImg.removeAttribute('src');
        document.body.style.overflow = '';
      };

      Array.prototype.forEach.call(document.querySelectorAll('.gallery figure'), function (fig) {
        fig.addEventListener('click', function () {
          var img = fig.querySelector('img');
          var cap = fig.querySelector('figcaption');
          if (img) { openBox(img.getAttribute('src'), cap ? cap.textContent.trim() : ''); }
        });
      });

      box.addEventListener('click', function (e) {
        if (e.target === box || e.target.classList.contains('close')) { closeBox(); }
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && box.classList.contains('open')) { closeBox(); }
      });
    }

    /* ---------- 7. 滚动显现动画 ---------- */
    var revealables = document.querySelectorAll('[data-reveal]');
    if (revealables.length) {
      if (!('IntersectionObserver' in window)) {
        Array.prototype.forEach.call(revealables, function (el) { el.style.opacity = 1; });
      } else {
        var io = new IntersectionObserver(function (entries) {
          entries.forEach(function (en) {
            if (en.isIntersecting) {
              en.target.style.transition = 'opacity .5s ease, transform .5s ease';
              en.target.style.opacity = '1';
              en.target.style.transform = 'none';
              io.unobserve(en.target);
            }
          });
        }, { threshold: 0.08 });
        Array.prototype.forEach.call(revealables, function (el) {
          el.style.opacity = '0';
          el.style.transform = 'translateY(14px)';
          io.observe(el);
        });
      }
    }
  });
})();
