import sys
import unittest

from greenlet import greenlet


def switch(*args):
    return greenlet.getcurrent().parent.switch(*args)


class ThrowTests(unittest.TestCase):
    def test_class(self):
        def f():
            try:
                switch("ok")
            except RuntimeError:
                switch("ok")
                return
            switch("fail")
        g = greenlet(f)
        res = g.switch()
        self.assertEqual(res, "ok")
        res = g.throw(RuntimeError)
        self.assertEqual(res, "ok")

    def test_val(self):
        def f():
            try:
                switch("ok")
            except RuntimeError:
                val = sys.exc_info()[1]
                if str(val) == "ciao":
                    switch("ok")
                    return
            switch("fail")

        g = greenlet(f)
        res = g.switch()
        self.assertEqual(res, "ok")
        res = g.throw(RuntimeError("ciao"))
        self.assertEqual(res, "ok")

        g = greenlet(f)
        res = g.switch()
        self.assertEqual(res, "ok")
        res = g.throw(RuntimeError, "ciao")
        self.assertEqual(res, "ok")

    def test_kill(self):
        def f():
            switch("ok")
            switch("fail")
        g = greenlet(f)
        res = g.switch()
        self.assertEqual(res, "ok")
        res = g.throw()
        self.assertTrue(isinstance(res, greenlet.GreenletExit))
        self.assertTrue(g.dead)
        res = g.throw()    # immediately eaten by the already-dead greenlet
        self.assertTrue(isinstance(res, greenlet.GreenletExit))

    def test_throw_goes_to_original_parent(self):
        main = greenlet.getcurrent()

        def f1():
            try:
                main.switch("f1 ready to catch")
            except IndexError:
                return "caught"
            else:
                return "normal exit"

        def f2():
            main.switch("from f2")

        g1 = greenlet(f1)
        g2 = greenlet(f2, parent=g1)
        self.assertRaises(IndexError, g2.throw, IndexError)
        self.assertTrue(g2.dead)
        self.assertTrue(g1.dead)

        g1 = greenlet(f1)
        g2 = greenlet(f2, parent=g1)
        res = g1.switch()
        self.assertEqual(res, "f1 ready to catch")
        res = g2.throw(IndexError)
        self.assertEqual(res, "caught")
        self.assertTrue(g2.dead)
        self.assertTrue(g1.dead)

        g1 = greenlet(f1)
        g2 = greenlet(f2, parent=g1)
        res = g1.switch()
        self.assertEqual(res, "f1 ready to catch")
        res = g2.switch()
        self.assertEqual(res, "from f2")
        res = g2.throw(IndexError)
        self.assertEqual(res, "caught")
        self.assertTrue(g2.dead)
        self.assertTrue(g1.dead)

    def test_non_traceback_param(self):
        with self.assertRaises(TypeError) as exc:
            greenlet.getcurrent().throw(
                Exception,
                Exception(),
                self
            )
        self.assertEqual(str(exc.exception),
                         "throw() third argument must be a traceback object")

    def test_instance_of_wrong_type(self):
        with self.assertRaises(TypeError) as exc:
            greenlet.getcurrent().throw(
                Exception(),
                BaseException()
            )

        self.assertEqual(str(exc.exception),
                         "instance exception may not have a separate value")

    def test_not_throwable(self):
        with self.assertRaises(TypeError) as exc:
            greenlet.getcurrent().throw(
                "abc"
            )
        self.assertEqual(str(exc.exception),
                         "exceptions must be classes, or instances, not str")
