import numpy as np
from scipy import sparse
import _pyift
from typing import Optional, Tuple, Dict


def seed_competition(seeds: np.ndarray, image: Optional[np.ndarray] = None, graph: Optional[sparse.csr_matrix] = None,
                     image_3d: bool = False) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Performs the shortest path classification from the `seeds` nodes
    using the image foresting transform algorithm [1]_.

    Parameters
    ----------
    seeds : array_like
        Positive values are the labels and shortest path sources,
        non-positives are ignored.
    image : array_like, optional
        Image data, seed competition is performed in the image grid graph,
        mutual exclusive with `graph`.
    graph : csr_matrix, optional
        Sparse graph, seed competition is performed in the given graph,
        mutual exclusive with `image`.
    image_3d : bool, optional
        Indicates if it is a 3D image or a 2D image with multiple bands,
        by default 'False'


    Returns
    -------
    array_like, array_like, array_like, array_like
        Image foresting transform costs, roots, predecessors and labels maps.

    Examples
    --------

    Image grid:

    >>> import numpy as np
    >>> from pyift.shortestpath import seed_competition
    >>>
    >>> seeds = np.array([[1, 0, 0],
    >>>                   [0, 0, 0],
    >>>                   [0, 2, 0]])
    >>> image = np.empty((3, 3, 2))
    >>> image[:, :, 0] = np.array([[1, 2, 3],
    >>>                            [2, 3, 4],
    >>>                            [2, 2, 3]])
    >>> image[:, :, 1] = np.array([[5, 6, 8],
    >>>                            [6, 8, 9],
    >>>                            [8, 9, 9]])
    >>> seed_competition(seeds, image=image)

    Sparse graph:

    >>> import numpy as np
    >>> from scipy.sparse import csgraph
    >>> from pyift.shortestpath import seed_competition
    >>>
    >>> seeds = np.array([1, 0, 0, 0, 2])
    >>> graph = csgraph.csgraph_from_dense([[0, 3, 2, 0, 0],
    >>>                                     [3, 0, 0, 3, 1],
    >>>                                     [2, 0, 0, 3, 0],
    >>>                                     [0, 3, 3, 0, 2],
    >>>                                     [0, 1, 0, 2, 0]])
    >>> seed_competition(seeds, graph=graph)

    References
    ----------
    .. [1] Falcão, Alexandre X., Jorge Stolfi, and Roberto de Alencar Lotufo. "The image foresting transform:
           Theory, algorithms, and applications." IEEE transactions on pattern analysis and
           machine intelligence 26.1 (2004): 19-29.

    """

    if image is None and graph is None:
        raise ValueError('`image` or `graph` must be provided.')

    if image is not None and graph is not None:
        raise ValueError('`image` and `graph` present, only one must be provided.')

    if image is not None:
        if not isinstance(image, np.ndarray):
            raise TypeError('`image` must be a `ndarray`.')

        if image.ndim < 2 or image.ndim > 4:
            raise ValueError('`image` must be a 2, 3 or 4-dimensional array, %d found.' % image.ndim)

        if image.ndim == 2:
            if image_3d:
                raise ValueError('2-dimensional array cannot be converted to an 3D grid.')
            else:
                image = np.expand_dims(image, 2)

        elif image.ndim == 3 and image_3d:
            image = np.expand_dims(image, 3)

        if image.shape[:-1] != seeds.shape:
            raise ValueError('`image` grid and `seeds` must have the same dimensions, %r and %r found.' %
                             (image.shape[:-1], seeds.shape))

        return _pyift.seed_competition_grid(image, seeds)

    # graph is provided
    if not isinstance(graph, sparse.csr_matrix):
        raise TypeError('`graph` must be a `csr_matrix`.')

    if graph.shape[0] != graph.shape[1]:
        raise ValueError('`graph` must be a square adjacency matrix, current shape %r.' % graph.shape)

    if seeds.ndim != 1:
        raise ValueError('`seeds` must be a 1-dimensional array, %d found.' % seeds.ndim)

    if seeds.shape[0] != graph.shape[0]:
        raise ValueError('`graph` and `seeds` dimensions does not match, %d and %d found.' %
                         (graph.shape[0], seeds.shape[0]))

    return _pyift.seed_competition_graph(graph.data, graph.indices, graph.indptr, seeds)


def dynamic_arc_weight(seeds: np.ndarray, image: np.ndarray, image_3d: bool = False,
                       mode: str = 'root', alpha: float = 0.5
                       ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[Tuple, np.ndarray]]:
    """
    Performs the image foresting transform classification from the `seeds` nodes with dynamic arc-weights [2]_.

    Parameters
    ----------
    seeds : array_like
        Positive values are the labels and shortest path sources,
        non-positives are ignored.
    image : array_like, optional
        Image data, seed competition is performed in the image grid graph.
    image_3d : bool, optional
        Indicates if it is a 3D image or a 2D image with multiple bands,
        by default 'False'.
    mode : {'root', 'label', 'exp'}, default='root'
        Indicates the average computation policy.
    alpha : float, optional
        Parameter of weight decay for exponential averaging, only valid
        when `mode` == 'exp'.

    Returns
    -------
    array_like, array_like, array_like, array_like, Union[array_like, dict]
        Image foresting transform costs, roots, predecessors, labels maps and a dictionary
        containing the average and size of each optimum-path tree.

    Examples
    --------

    >>> import numpy as np
    >>> from pyift.shortestpath import dynamic_arc_weight
    >>>
    >>> seeds = np.array([[1, 0, 0],
    >>>                   [0, 0, 0],
    >>>                   [0, 2, 0]])
    >>> image = np.empty((3, 3, 2))
    >>> image[:, :, 0] = np.array([[1, 2, 3],
    >>>                            [2, 3, 4],
    >>>                            [2, 2, 3]])
    >>> image[:, :, 1] = np.array([[5, 6, 8],
    >>>                            [6, 8, 9],
    >>>                            [8, 9, 9]])
    >>> dynamic_arc_weight(seeds, image)

    References
    ----------
    .. [2] Bragantini, Jordão, et al. "Graph-based image segmentation using dynamic trees."
           Iberoamerican Congress on Pattern Recognition. Springer, Cham, 2018.

    """
    allowed_modes = ('exp', 'label', 'root')
    if mode not in allowed_modes:
        raise ValueError('`mode` must belong to %r' % (allowed_modes, ))

    if not isinstance(image, np.ndarray):
        raise TypeError('`image` must be a `ndarray`.')

    if image.ndim < 2 or image.ndim > 4:
        raise ValueError('`image` must be a 2, 3 or 4-dimensional array, %d found.' % image.ndim)

    if alpha < 0 or alpha > 1:
        raise ValueError('`alpha` must be between 0 and 1')

    if image.ndim == 2:
        if image_3d:
            raise ValueError('2-dimensional array cannot be converted to an 3D grid.')
        else:
            image = np.expand_dims(image, 2)

    elif image.ndim == 3 and image_3d:
        image = np.expand_dims(image, 3)

    if image.shape[:-1] != seeds.shape:
        raise ValueError('`image` grid and `seeds` must have the same dimensions, %r and %r found.' %
                         (image.shape[:-1], seeds.shape))
    if mode == 'exp':
        return _pyift.dynamic_arc_weight_grid_exp_decay(image, seeds, alpha)
    elif mode == 'label':
        return _pyift.dynamic_arc_weight_grid_label(image, seeds)
    elif mode == 'root':
        return _pyift.dynamic_arc_weight_grid_root(image, seeds)
    else:
        raise NotImplementedError


def distance_transform_edt(mask: np.ndarray, scales: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the euclidean distance transform using the IFT algorithm [3].

    Parameters
    ----------
    mask : array_like
        Binary mask of regions to compute the EDT from border.
    scales : array_like, optional
        Distance scale for each image axis.

    Returns
    -------
    array_like
        Euclidean distance transform mapping from boundaries.

    Examples
    --------

    >>> import numpy as np
    >>> from pyift.shortestpath import distance_transform_edt
    >>>
    >>> mask = np.array([[0, 0, 0, 0, 0, 0],
    >>>                  [0, 1, 0, 1, 0, 0],
    >>>                  [0, 1, 1, 1, 1, 0],
    >>>                  [0, 1, 1, 1, 1, 0],
    >>>                  [0, 1, 1, 0, 1, 0],
    >>>                  [0, 0, 0, 0, 0, 0]], dtype=bool)
    >>>
    >>> distance_transform_edt(mask)

    References
    ----------
    .. [3] Falcão, Alexandre X., Jorge Stolfi, and Roberto de Alencar Lotufo. "The image foresting transform:
           Theory, algorithms, and applications." IEEE transactions on pattern analysis and
           machine intelligence 26.1 (2004): 19-29.

    """
    if not isinstance(mask, np.ndarray):
        raise TypeError('`mask` must be a `ndarray`.')

    if scales is None:
        scales = np.ones(3)

    if not isinstance(scales, np.ndarray):
        scales = np.asarray(scales)

    if scales.ndim != 1:
        raise ValueError('`scales` must be a 1-dimensional array.')

    if scales.shape[0] == 2:
        scales = np.array((1, scales[0], scales[1]))

    if scales.shape[0] != 3:
        raise ValueError('`scales` must be a 2 or 3-dimensional array, %d found.' % scales.ndim)

    if mask.ndim < 2 or mask.ndim > 3:
        raise ValueError('`image` must be a 2 or 3-dimensional array, %d found.' % mask.ndim)

    # distance and nearest points
    distance, _ = _pyift.euclidean_distance_transform_grid(mask.astype(bool), scales)
    return distance


def watershed_from_minima(image: np.ndarray, mask: Optional[np.ndarray] = None,
                          penalization: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes the watershed transform on grayscales images from minimum with the IFT algorithm [4].

    Parameters
    ----------
    image : array_like
        Grayscale 2D or 3D image.
    mask : array_like, optional
        Binary mask of regions to compute the watershed transform.
    penalization : float
        Parameter to adjust the catchment basins of watershed. Greater the value the more the neighboring
        minima will merge into a single region.

    Returns
    -------
    array_like, array_like
        Optimum-path costs and roots (minima) from watershed basins.

    Examples
    --------

    >>> import numpy as np
    >>> from pyift.shortestpath import watershed_from_minima
    >>>
    >>> image = np.array([[7, 8, 9, 8, 8, 8],
    >>>                   [6, 3, 9, 0, 9, 8],
    >>>                   [4, 1, 6, 1, 1, 8],
    >>>                   [3, 3, 5, 4, 4, 8],
    >>>                   [1, 0, 7, 2, 2, 8],
    >>>                   [6, 8, 9, 8, 9, 9]])
    >>>
    >>> watershed_from_minima(image)

    References
    ----------
    .. [4] Falcão, Alexandre X., Jorge Stolfi, and Roberto de Alencar Lotufo. "The image foresting transform:
           Theory, algorithms, and applications." IEEE transactions on pattern analysis and
           machine intelligence 26.1 (2004): 19-29.

    """
    if not isinstance(image, np.ndarray):
        raise TypeError('`image` must be a `ndarray`.')

    if mask is None:
        mask = np.ones_like(image, dtype=bool)

    if not isinstance(mask, np.ndarray):
        raise TypeError('`mask` must be a `ndarray`.')

    if image.shape != mask.shape:
        raise ValueError('`image` and `mask` must have the same dimensions, %r and %r found.' %
                         (image.shape, mask.shape))

    if image.ndim < 2 or image.ndim > 3:
        raise ValueError('`image` must be a 2 or 3-dimensional array, %d found.' % image.ndim)

    return _pyift.watershed_from_minima_grid(image, mask.astype(bool), penalization)
