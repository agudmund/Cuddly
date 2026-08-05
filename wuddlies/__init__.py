#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cuddly - wuddlies/__init__.py the naming channel's front door
-The last of the name channels opened beside an infinite pool and promised no soul would go unnamed, For Enjoying
-Built using a single shared braincell by Yours Truly and various Intelligences

The Wuddlies naming channel: a tiny own-trained character-level weight (the
librarian) that supplies name material to the schema whose true workings
live off-disk in the dish. This package is a SOCKET, never an integration:
opaque seed in, optional meaning-free condition floats in, names out. Fully
offline at inference by construction. Corpus provenance: onomaverse/names
(CC-BY-4.0) and Hobson/surname-nationality (MIT), harvested 2026-08-05;
attribution lives in wuddlies/data/raw alongside the licenses.
"""

from wuddlies.model import WuddlyModel, load_model, save_model

__all__ = ["WuddlyModel", "load_model", "save_model"]
