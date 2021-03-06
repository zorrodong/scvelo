from .utils import is_categorical, update_axes, set_label, set_title, default_basis, default_color, \
    default_color_map, interpret_colorkey, get_components, set_colorbar, savefig
from .docs import doc_scatter, doc_params
import scanpy.api.pl as scpl
import matplotlib.pyplot as pl
import numpy as np
import pandas as pd


@doc_params(scatter=doc_scatter)
def scatter(adata, x=None, y=None, basis=None, color=None, use_raw=None, layer=None, color_map=None, colorbar=False,
            palette=None, size=5, alpha=1, perc=None, sort_order=True, groups=None, components=None, projection='2d',
            legend_loc='none', legend_fontsize=None, legend_fontweight=None, right_margin=None, left_margin=None,
            xlabel=None, ylabel=None, title=None, fontsize=None, figsize=(7,5), dpi=100, frameon=None, show=True,
            save=None, ax=None, **kwargs):
    """\
    Scatter plot along observations or variables axes.

    Arguments
    ---------
    adata: :class:`~anndata.AnnData`
        Annotated data matrix.
    x: `str`, `np.ndarray` or `None` (default: `None`)
        x coordinate
    y: `str`, `np.ndarray` or `None` (default: `None`)
        y coordinate
    {scatter}

    Returns
    -------
        If `show==False` a `matplotlib.Axis`
    """
    colors = pd.unique(color) if isinstance(color, (list, tuple, np.ndarray, np.record)) else [color]
    layers = pd.unique(layer) if isinstance(layer, (list, tuple, np.ndarray, np.record)) else [layer]

    if len(colors) > 1:
        for i, gs in enumerate(pl.GridSpec(1, len(colors), pl.figure(None, (figsize[0]*len(colors), figsize[1]), dpi=dpi))):
            scatter(adata, x=x, y=y, basis=basis, layer=layer, color=colors[i], xlabel=xlabel, ylabel=ylabel, color_map=color_map,
                    perc=perc, size=size, alpha=alpha, fontsize=fontsize, frameon=frameon, title=title, show=False,
                    colorbar=colorbar, components=components, figsize=figsize, dpi=dpi, save=None, ax=pl.subplot(gs),
                    use_raw=use_raw, sort_order=sort_order, groups=groups, projection=projection,
                    legend_loc=legend_loc, legend_fontsize=legend_fontsize, legend_fontweight=legend_fontweight,
                    palette=palette, right_margin=right_margin, left_margin=left_margin, **kwargs)
        if isinstance(save, str): savefig('' if basis is None else basis, dpi=dpi, save=save, show=show)
        if show: pl.show()
        else: return ax

    elif len(layers) > 1:
        for i, gs in enumerate(pl.GridSpec(1, len(layers), pl.figure(None, (figsize[0] * len(layers), figsize[1]), dpi=dpi))):
            scatter(adata, x=x, y=y, basis=basis, layer=layers[i], color=color, xlabel=xlabel, ylabel=ylabel, color_map=color_map,
                    perc=perc, size=size, alpha=alpha, fontsize=fontsize, frameon=frameon, title=title, show=False,
                    colorbar=colorbar, components=components, figsize=figsize, dpi=dpi, save=None, ax=pl.subplot(gs),
                    use_raw=use_raw, sort_order=sort_order, groups=groups, projection=projection,
                    legend_loc=legend_loc, legend_fontsize=legend_fontsize, legend_fontweight=legend_fontweight,
                    palette=palette, right_margin=right_margin, left_margin=left_margin, **kwargs)
        if isinstance(save, str): savefig('' if basis is None else basis, dpi=dpi, save=save, show=show)
        if show: pl.show()
        else: return ax

    else:
        ax = pl.figure(None, figsize, dpi=dpi).gca() if ax is None else ax
        color, layer = colors[0], layers[0]
        color = default_color(adata) if color is None else color
        color_map = default_color_map(adata, color) if color_map is None else color_map

        is_embedding = (x is None) | (y is None)
        basis = default_basis(adata) if basis is None and is_embedding else basis

        if is_categorical(adata, color) and is_embedding:
            ax = scpl.scatter(adata, basis=basis, color=color, use_raw=use_raw, sort_order=sort_order, alpha=alpha,
                              groups=groups, components=components, projection=projection, legend_loc=legend_loc,
                              legend_fontsize=legend_fontsize, legend_fontweight=legend_fontweight, color_map=color_map,
                              palette=palette, right_margin=right_margin, left_margin=left_margin, size=size,
                              title=title, frameon=frameon, show=False, save=None, ax=ax, **kwargs)

        else:
            if is_embedding:
                X_emb = adata.obsm['X_' + basis][:, get_components(components)]
                x, y = X_emb[:, 0], X_emb[:, 1]
            elif isinstance(x, str) and isinstance(y, str) and x in adata.var_names and y in adata.var_names:
                x = adata[:, x].layers[layer] if layer in adata.layers.keys() else adata[:, x].X
                y = adata[:, y].layers[layer] if layer in adata.layers.keys() else adata[:, y].X

            c = interpret_colorkey(adata, color, layer, perc)
            if layer is not None and 'velocity' in layer and isinstance(color, str) and color in adata.var_names:
                ub = np.percentile(np.abs(c), 98)
                kwargs.update({"vmin": -ub, "vmax": ub})

            pl.scatter(x, y, c=c, cmap=color_map, s=size, alpha=alpha, zorder=0, **kwargs)

            set_label(xlabel, ylabel, fontsize, basis)
            set_title(title, layer, color, fontsize)
            ax = update_axes(ax, fontsize, is_embedding, frameon)

            if colorbar and not is_categorical(adata, color): set_colorbar(ax)

        if isinstance(save, str): savefig('' if basis is None else basis, dpi=dpi, save=save, show=show)
        if show: pl.show()
        else: return ax