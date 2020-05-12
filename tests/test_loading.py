import copy
import os.path as osp
from pathlib import Path

import mmcv
import numpy as np
import pytest
from mmedit.datasets.pipelines import (LoadAlpha, LoadImageFromFile,
                                       LoadImageFromFileList, LoadMask,
                                       LoadPairedImageFromFile,
                                       RandomLoadResizeBg)


def test_load_image_from_file():
    path_baboon = Path(__file__).parent / 'data' / 'gt' / 'baboon.png'
    img_baboon = mmcv.imread(str(path_baboon), flag='color')
    path_baboon_x4 = Path(__file__).parent / 'data' / 'lq' / 'baboon_x4.png'
    img_baboon_x4 = mmcv.imread(str(path_baboon_x4), flag='color')

    # read gt image
    # input path is Path object
    results = dict(gt_path=path_baboon)
    config = dict(io_backend='disk', key='gt')
    image_loader = LoadImageFromFile(**config)
    results = image_loader(results)
    assert results['gt'].shape == (480, 500, 3)
    np.testing.assert_almost_equal(results['gt'], img_baboon)
    assert results['gt_path'] == str(path_baboon)
    # input path is str
    results = dict(gt_path=str(path_baboon))
    results = image_loader(results)
    assert results['gt'].shape == (480, 500, 3)
    np.testing.assert_almost_equal(results['gt'], img_baboon)
    assert results['gt_path'] == str(path_baboon)

    # read lq image
    # input path is Path object
    results = dict(lq_path=path_baboon_x4)
    config = dict(io_backend='disk', key='lq')
    image_loader = LoadImageFromFile(**config)
    results = image_loader(results)
    assert results['lq'].shape == (120, 125, 3)
    np.testing.assert_almost_equal(results['lq'], img_baboon_x4)
    assert np.sum(np.abs(results['lq'] - img_baboon_x4)) < 0.001
    assert results['lq_path'] == str(path_baboon_x4)
    # input path is str
    results = dict(lq_path=str(path_baboon_x4))
    results = image_loader(results)
    assert results['lq'].shape == (120, 125, 3)
    np.testing.assert_almost_equal(results['lq'], img_baboon_x4)
    assert results['lq_path'] == str(path_baboon_x4)
    assert repr(image_loader) == (
        image_loader.__class__.__name__ +
        ('(io_backend=disk, key=lq, '
         'flag=color, save_original_img=False)'))

    results = dict(lq_path=path_baboon_x4)
    config = dict(
        io_backend='disk', key='lq', flag='grayscale', save_original_img=True)
    image_loader = LoadImageFromFile(**config)
    results = image_loader(results)
    assert results['lq'].shape == (120, 125, 1)
    assert results['lq_ori_shape'] == (120, 125, 1)
    np.testing.assert_almost_equal(results['ori_lq'], results['lq'])
    assert id(results['ori_lq']) != id(results['lq'])


def test_load_image_from_file_list():
    path_baboon = Path(__file__).parent / 'data' / 'gt' / 'baboon.png'
    img_baboon = mmcv.imread(str(path_baboon), flag='color')
    path_baboon_x4 = Path(__file__).parent / 'data' / 'lq' / 'baboon_x4.png'
    img_baboon_x4 = mmcv.imread(str(path_baboon_x4), flag='color')

    # input path is Path object
    results = dict(lq_path=[path_baboon_x4, path_baboon])
    config = dict(io_backend='disk', key='lq')
    image_loader = LoadImageFromFileList(**config)
    results = image_loader(results)
    np.testing.assert_almost_equal(results['lq'][0], img_baboon_x4)
    np.testing.assert_almost_equal(results['lq'][1], img_baboon)
    assert results['lq_ori_shape'] == [(120, 125, 3), (480, 500, 3)]
    assert results['lq_path'] == [str(path_baboon_x4), str(path_baboon)]
    # input path is str
    results = dict(lq_path=[str(path_baboon_x4), str(path_baboon)])
    config = dict(io_backend='disk', key='lq')
    image_loader = LoadImageFromFileList(**config)
    results = image_loader(results)
    np.testing.assert_almost_equal(results['lq'][0], img_baboon_x4)
    np.testing.assert_almost_equal(results['lq'][1], img_baboon)
    assert results['lq_path'] == [str(path_baboon_x4), str(path_baboon)]

    # save ori_img
    results = dict(lq_path=[path_baboon_x4])
    config = dict(io_backend='disk', key='lq', save_original_img=True)
    image_loader = LoadImageFromFileList(**config)
    results = image_loader(results)
    np.testing.assert_almost_equal(results['lq'][0], img_baboon_x4)
    assert results['lq_ori_shape'] == [(120, 125, 3)]
    assert results['lq_path'] == [str(path_baboon_x4)]
    np.testing.assert_almost_equal(results['ori_lq'][0], img_baboon_x4)

    with pytest.raises(TypeError):
        # filepath should be list
        results = dict(lq_path=path_baboon_x4)
        image_loader(results)


class TestMattingLoading(object):

    @staticmethod
    def check_keys_contain(result_keys, target_keys):
        """Check if all elements in target_keys is in result_keys."""
        return set(target_keys).issubset(set(result_keys))

    @classmethod
    def setup_class(cls):
        data_prefix = osp.join(osp.dirname(__file__), 'data')
        ann_file = osp.join(data_prefix, 'test_list.json')
        data_infos = mmcv.load(ann_file)
        cls.results = dict()
        for data_info in data_infos:
            for key in data_info:
                cls.results[key] = osp.join(data_prefix, data_info[key])

    def test_load_alpha(self):
        target_keys = [
            'alpha', 'ori_alpha', 'ori_shape', 'img_shape', 'img_name'
        ]
        config = dict(io_backend='disk', key='alpha', flag='grayscale')
        results = copy.deepcopy(self.results)
        load_alpha = LoadAlpha(**config)
        for _ in range(2):
            load_alpha_results = load_alpha(results)
            assert self.check_keys_contain(load_alpha_results.keys(),
                                           target_keys)
            assert isinstance(load_alpha_results['alpha'], np.ndarray)
            assert load_alpha_results['alpha'].shape == (552, 800)

    def test_random_load_bg(self):
        target_keys = ['bg']

        results = dict(img_shape=(128, 128))
        random_load_bg = RandomLoadResizeBg('tests/data/bg')
        for _ in range(2):
            random_load_bg_results = random_load_bg(results)
            assert self.check_keys_contain(random_load_bg_results.keys(),
                                           target_keys)
            assert isinstance(random_load_bg_results['bg'], np.ndarray)
            assert random_load_bg_results['bg'].shape == (128, 128, 3)

        assert repr(random_load_bg) == random_load_bg.__class__.__name__ + (
            "(bg_dir='tests/data/bg')")


class TestInpaintLoading(object):

    @classmethod
    def setup_class(cls):
        cls.img_path = Path(__file__).parent.joinpath('data/image/test.png')
        cls.results = dict(img_info=dict(filename=cls.img_path))

    def test_load_mask(self):

        # test mask mode: set
        mask_config = dict(
            mask_list_file='./tests/data/mask_list.txt',
            prefix='./tests/data',
            io_backend='disk',
            flag='unchanged',
            file_client_kwargs=dict())

        set_loader = LoadMask('set', mask_config)
        class_name = set_loader.__class__.__name__
        assert repr(set_loader) == class_name + "(mask_mode='set')"
        for _ in range(2):
            results = dict()
            results = set_loader(results)
            gt_mask = mmcv.imread(
                './tests/data/mask/test.png', flag='unchanged')
            assert np.array_equal(results['mask'], gt_mask[..., 0:1])

        mask_config = dict(
            mask_list_file='./tests/data/mask_list_single_ch.txt',
            prefix='./tests/data',
            io_backend='disk',
            flag='unchanged',
            file_client_kwargs=dict())

        # test mask mode: set with input as single channel image
        set_loader = LoadMask('set', mask_config)
        results = dict()
        results = set_loader(results)
        gt_mask = mmcv.imread(
            './tests/data/mask/test_single_ch.png', flag='unchanged')
        gt_mask = np.expand_dims(gt_mask, axis=2)
        assert np.array_equal(results['mask'], gt_mask[..., 0:1])

        # test mask mode: ff
        mask_config = dict(
            img_shape=(256, 256),
            num_vertexes=(4, 12),
            mean_angle=1.2,
            angle_range=0.4,
            brush_width=(12, 40))

        ff_loader = LoadMask('ff', mask_config)
        results = dict()
        results = ff_loader(results)
        assert results['mask'].shape == (256, 256, 1)

        # test mask mode: irregular holes
        mask_config = dict(
            img_shape=(256, 256),
            num_vertexes=(4, 12),
            max_angle=4.,
            length_range=(10, 100),
            brush_width=(10, 40),
            area_ratio_range=(0.15, 0.5))

        irregular_loader = LoadMask('irregular', mask_config)
        results = dict()
        results = irregular_loader(results)
        assert results['mask'].shape == (256, 256, 1)

        # test mask mode: bbox
        mask_config = dict(img_shape=(256, 256), max_bbox_shape=128)

        bbox_loader = LoadMask('bbox', mask_config)
        results = dict()
        results = bbox_loader(results)
        assert results['mask'].shape == (256, 256, 1)

        with pytest.raises(NotImplementedError):
            loader = LoadMask('ooxx', mask_config)
            results = loader(results)


class TestGenerationLoading(object):

    @staticmethod
    def check_keys_contain(result_keys, target_keys):
        """Check if all elements in target_keys is in result_keys."""
        return set(target_keys).issubset(set(result_keys))

    @classmethod
    def setup_class(cls):
        cls.pair_path = osp.join(
            osp.dirname(__file__), 'data/paired/train/1.jpg')
        cls.results = dict(pair_path=cls.pair_path)
        cls.pair_img = mmcv.imread(str(cls.pair_path), flag='color')
        w = cls.pair_img.shape[1]
        new_w = w // 2
        cls.img_a = cls.pair_img[:, :new_w, :]
        cls.img_b = cls.pair_img[:, new_w:, :]
        cls.pair_shape = cls.pair_img.shape
        cls.img_shape = cls.img_a.shape
        cls.pair_shape_gray = (256, 512, 1)
        cls.img_shape_gray = (256, 256, 1)

    def test_load_paired_image_from_file(self):
        # RGB
        target_keys = [
            'pair_path', 'pair', 'pair_ori_shape', 'img_a_path', 'img_a',
            'img_a_ori_shape', 'img_b_path', 'img_b', 'img_b_ori_shape'
        ]
        config = dict(io_backend='disk', key='pair', flag='color')
        results = copy.deepcopy(self.results)
        load_paired_image_from_file = LoadPairedImageFromFile(**config)
        results = load_paired_image_from_file(results)

        assert self.check_keys_contain(results.keys(), target_keys)
        assert results['pair'].shape == self.pair_shape
        assert results['pair_ori_shape'] == self.pair_shape
        np.testing.assert_equal(results['pair'], self.pair_img)
        assert results['pair_path'] == self.pair_path
        assert results['img_a'].shape == self.img_shape
        assert results['img_a_ori_shape'] == self.img_shape
        np.testing.assert_equal(results['img_a'], self.img_a)
        assert results['img_a_path'] == self.pair_path
        assert results['img_b'].shape == self.img_shape
        assert results['img_b_ori_shape'] == self.img_shape
        np.testing.assert_equal(results['img_b'], self.img_b)
        assert results['img_b_path'] == self.pair_path

        # Grayscale & save_original_img
        target_keys = [
            'pair_path', 'pair', 'pair_ori_shape', 'ori_pair', 'img_a_path',
            'img_a', 'img_a_ori_shape', 'ori_img_a', 'img_b_path', 'img_b',
            'img_b_ori_shape', 'ori_img_b'
        ]
        config = dict(
            io_backend='disk',
            key='pair',
            flag='grayscale',
            save_original_img=True)
        results = copy.deepcopy(self.results)
        load_paired_image_from_file = LoadPairedImageFromFile(**config)
        results = load_paired_image_from_file(results)

        assert self.check_keys_contain(results.keys(), target_keys)
        assert results['pair'].shape == self.pair_shape_gray
        assert results['pair_ori_shape'] == self.pair_shape_gray
        np.testing.assert_equal(results['pair'], results['ori_pair'])
        assert id(results['ori_pair']) != id(results['pair'])
        assert results['pair_path'] == self.pair_path
        assert results['img_a'].shape == self.img_shape_gray
        assert results['img_a_ori_shape'] == self.img_shape_gray
        np.testing.assert_equal(results['img_a'], results['ori_img_a'])
        assert id(results['ori_img_a']) != id(results['img_a'])
        assert results['img_a_path'] == self.pair_path
        assert results['img_b'].shape == self.img_shape_gray
        assert results['img_b_ori_shape'] == self.img_shape_gray
        np.testing.assert_equal(results['img_b'], results['ori_img_b'])
        assert id(results['ori_img_b']) != id(results['img_b'])
        assert results['img_b_path'] == self.pair_path
