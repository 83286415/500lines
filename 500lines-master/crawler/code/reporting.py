"""Reporting subsystem for web crawler."""

import time


class Stats:
    """Record stats of various sorts."""

    def __init__(self):
        self.stats = {}

    def add(self, key, count=1):
        self.stats[key] = self.stats.get(key, 0) + count

    def report(self, file=None):
        for key, count in sorted(self.stats.items()):
            print('%10d' % count, key, file=file)


def report(crawler, file=None):
    """Print a report on all completed URLs."""
    t1 = crawler.t1 or time.time()  # 爬取结束时间
    dt = t1 - crawler.t0  # dt: 爬取经历时间  t0:开始爬取时间
    if dt and crawler.max_tasks:
        speed = len(crawler.done) / dt / crawler.max_tasks  # done是个列表，每个元素存储了url及其相关信息的namedtuple
    else:
        speed = 0
    stats = Stats()
    print('*** Report ***', file=file)  # file此处是将打印输出到文件file
    try:
        show = list(crawler.done)  # namedtuple列表化
        show.sort(key=lambda _stat: _stat.url)  # 按照done命名元组里的url名称排序
        for stat in show:
            url_report(stat, stats, file=file)  # 打印每个url元素相关分类信息；file此处是将打印输出到文件file
    except KeyboardInterrupt:
        print('\nInterrupted', file=file)  # file此处是将打印输出到文件file
    print('Finished', len(crawler.done),
          'urls in %.3f secs' % dt,
          '(max_tasks=%d)' % crawler.max_tasks,
          '(%.3f urls/sec/task)' % speed,
          file=file)
    stats.report(file=file)  # 打印统计信息
    print('Todo:', crawler.q.qsize(), file=file)
    print('Done:', len(crawler.done), file=file)
    print('Date:', time.ctime(), 'local time', file=file)


def url_report(stat, stats, file=None):
    """Print a report on the state for this URL.

    Also update the Stats instance.
    """
    if stat.exception:  # 若done列表里元素中存在exception，则stats实例中的fail会+1
        stats.add('fail')
        stats.add('fail_' + str(stat.exception.__class__.__name__))
        print(stat.url, 'error', stat.exception, file=file)  # error后面跟的是报错信息
    elif stat.next_url:  # 若url是个跳转
        stats.add('redirect')
        print(stat.url, stat.status, 'redirect', stat.next_url,
              file=file)
    elif stat.content_type == 'text/html':  # 'text/html', 'application/xml', 'text/plain'
        stats.add('html')
        stats.add('html_bytes', stat.size)
        print(stat.url, stat.status,
              stat.content_type, stat.encoding,
              stat.size,
              '%d/%d' % (stat.num_new_urls, stat.num_urls),
              file=file)  # TODO: why elif here
    else:
        if stat.status == 200:
            stats.add('other')
            stats.add('other_bytes', stat.size)
        else:
            stats.add('error')
            stats.add('error_bytes', stat.size)
            stats.add('status_%s' % stat.status)
        print(stat.url, stat.status,
              stat.content_type, stat.encoding,
              stat.size,
              file=file)
