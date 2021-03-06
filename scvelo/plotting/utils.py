from .. import settings
import numpy as np
import matplotlib.pyplot as pl
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from scanpy.plotting.utils import savefig_or_show, default_palette, adjust_palette
from matplotlib.colors import is_color_like
from pandas.api.types import is_categorical as cat
from scipy.sparse import issparse


def is_categorical(adata, c):
    adata._sanitize()  # Indentify array of categorical type and transform where applicable
    return isinstance(c, str) and (c in adata.obs.keys() and cat(adata.obs[c]) or is_color_like(c))


def default_basis(adata):
    keys = [key for key in ['pca', 'tsne', 'umap'] if 'X_' + key in adata.obsm.keys()]
    if len(keys) > 0:
        return keys[-1]
    else:
        raise ValueError('No basis specified')


def update_axes(ax, fontsize, is_embedding, frameon):
    frameon = settings._frameon if frameon is None else frameon
    if frameon:
        if is_embedding:
            ax.tick_params(which='both', bottom=False, left=False, labelbottom=False, labelleft=False)
        else:
            ax.xaxis.set_major_locator(MaxNLocator(nbins=3, integer=True))
            ax.yaxis.set_major_locator(MaxNLocator(nbins=3, integer=True))
            labelsize = int(fontsize * .75) if fontsize is not None else None
            ax.tick_params(axis='both', which='major', labelsize=labelsize)
    else:
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.tick_params(which='both', bottom=False, left=False, labelbottom=False, labelleft=False)
        ax.set_frame_on(False)
    return ax


def set_label(xlabel, ylabel, fontsize=None, basis=None):
    if isinstance(xlabel, str) and isinstance(ylabel, str):
        pl.xlabel(xlabel, fontsize=fontsize)
        pl.ylabel(ylabel, fontsize=fontsize)
    elif basis is not None:
        component_name = ('DC' if basis == 'diffmap' else 'tSNE' if basis == 'tsne' else 'UMAP' if basis == 'umap'
        else 'PC' if basis == 'pca' else basis.replace('draw_graph_', '').upper() if 'draw_graph' in basis else basis)
        pl.xlabel(component_name + '1')
        pl.ylabel(component_name + '2')


def set_title(title, layer=None, color=None, fontsize=None):
    if isinstance(title, str):
        pl.title(title, fontsize=fontsize)
    elif isinstance(layer, str) and isinstance(color, str):
        pl.title(color + ' ' + layer, fontsize=fontsize)
    elif isinstance(color, str):
        pl.title(color, fontsize=fontsize)


def set_frame(ax, frameon):
    frameon = settings._frameon if frameon is None else frameon
    if not frameon:
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_frame_on(False)
    return ax


def default_color(adata):
    return 'clusters' if 'clusters' in adata.obs.keys() else 'louvain' if 'louvain' in adata.obs.keys() else 'grey'


def default_color_map(adata, c):
    return 'viridis_r' if isinstance(c, str) and c in adata.obs.keys() and not is_categorical(adata, c)\
                          and adata.obs[c].min() == 0 and adata.obs[c].max() == 1 else 'RdBu_r'


def clip(c, perc=None):
    if isinstance(perc, int): perc = [perc, 100] if perc < 50 else perc[0, perc]
    lb, ub = np.percentile(c, perc)
    return np.clip(c, lb, ub)


def get_colors(adata, c):
    if is_color_like(c):
        return c
    else:
        if c+'_colors' not in adata.uns.keys():
            palette = default_palette(None)
            palette = adjust_palette(palette, length=len(adata.obs[c].cat.categories))
            adata.uns[c + '_colors'] = palette[:len(adata.obs[c].cat.categories)].by_key()['color']
        cluster_ix = adata.obs[c].cat.codes
        return np.array([adata.uns[c + '_colors'][cluster_ix[i]] for i in range(adata.n_obs)])


def interpret_colorkey(adata, c=None, layer=None, perc=None):
    if c is None: c = default_color(adata)
    if is_categorical(adata, c): c = get_colors(adata, c)
    elif isinstance(c, str):
        if c in adata.obs.keys():  # color by observation key
            c = adata.obs[c]
        elif c in adata.var_names:  # color by var in specific layer
            c = adata[:, c].layers[layer] if layer in adata.layers.keys() else adata[:, c].X
            c = c.A.flatten() if issparse(c) else c
        if perc is not None: c = clip(c, perc=perc)
    elif len(np.array(c).flatten()) == adata.n_obs:  # continuous coloring
        c = np.array(c).flatten()
        if perc is not None: c = clip(c, perc=perc)
    else:
        raise ValueError('color key is invalid! pass valid observation annotation or a gene name')
    return c


def get_components(components=None):
    if components is None: components = '1,2'
    if isinstance(components, str): components = components.split(',')
    return np.array(components).astype(int) - 1


def set_colorbar(ax, orientation='vertical'):
    cb = pl.colorbar(orientation=orientation, cax=inset_axes(ax, width="2%", height="30%", loc=4, borderpad=0))
    cb.set_alpha(1)
    cb.draw_all()
    cb.locator = MaxNLocator(nbins=3, integer=True)
    cb.update_ticks()


def savefig(writekey, show=False, dpi=None, save=None):
    """Save current figure to file.
    """
    savefig_or_show('velocity_' + writekey + '_' if writekey != '' else 'velocity_', dpi=dpi, save=save, show=show)


def hist(arrays, bins, alpha=.5, colors=None, labels=None, xlabel=None, ylabel=None, ax=None):
    ax = pl.figure(None, (8, 4), dpi=120) if ax is None else ax
    arrays = arrays if isinstance(arrays, (list, tuple, np.ndarray, np.record)) else [arrays]

    palette = default_palette(None)[::3][:len(arrays)].by_key()['color']
    colors = palette if colors is None or len(colors) < len(arrays) else colors

    for i, array in enumerate(arrays):
        pl.hist(array, bins=bins, alpha=alpha, color=colors[i], label=labels[i] if labels is not None else None)
    pl.legend()
    pl.xlabel(xlabel if xlabel is not None else '')
    pl.ylabel(ylabel if xlabel is not None else '')
    pl.show()


# def phase(adata, var=None, x=None, y=None, color='louvain', fits='all', xlabel='spliced', ylabel='unspliced',
#           fontsize=None, show=True, ax=None, **kwargs):
#     if isinstance(var, str) and (var in adata.var_names):
#         if (x is None) or (y is None):
#             ix = np.where(adata.var_names == var)[0][0]
#             x, y = adata.layers['Ms'][:, ix], adata.layers['Mu'][:, ix]
#     else:
#         ValueError('var not found in adata.var_names.')
#
#     ax = scatter(adata, x=x, y=y, color=color, frameon=True, title=var, xlabel=xlabel, ylabel=ylabel, ax=ax, **kwargs)
#
#     xnew = np.linspace(0, x.max() * 1.02)
#     fits = adata.layers.keys() if fits == 'all' else fits
#     fits = [fit for fit in fits if 'velocity' in fit]
#     for fit in fits:
#         linestyle = '--' if 'stochastic' in fit else '-'
#         pl.plot(xnew, adata.var[fit+'_gamma'][ix] / adata.var[fit+'_beta'][ix] * xnew
#                 + adata.var[fit+'_offset'][ix] / adata.var[fit+'_beta'][ix], c='k', linestyle=linestyle)
#
#     if show: pl.show()
#     else: return ax