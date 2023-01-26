# %%
import math
import typing as ty
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as nn_init
import zero
from torch import Tensor

import lib
import os

#os.environ["CUDA_VISIBLE_DEVICES"] = "0"


# %%
class Factorizer_col(nn.Module):
    category_offsets: ty.Optional[Tensor]

    def __init__(
            self,
            d_numerical: int,
            categories: ty.Optional[ty.List[int]],
            d_token: int,
            bias: bool,
            f: int,
    ) -> None:
        super().__init__()
        if categories is None:
            d_bias = d_numerical
            self.category_offsets = None
            self.category_embeddings = None
        else:
            d_bias = d_numerical + len(categories)
            category_offsets = torch.tensor([0] + categories[:-1]).cumsum(0)
            self.register_buffer('category_offsets', category_offsets)
            self.category_embeddings = nn.Embedding(sum(categories), d_token)
            nn_init.kaiming_uniform_(self.category_embeddings.weight, a=math.sqrt(5))
            print(f'{self.category_embeddings.weight.shape=}')
        self.f = f
        # take [CLS] token into account
        self.weight = nn.Parameter(Tensor(d_numerical + f, d_token))
        self.bias = nn.Parameter(Tensor(d_bias, d_token)) if bias else None
        # The initialization is inspired by nn.Linear
        nn_init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if self.bias is not None:
            nn_init.kaiming_uniform_(self.bias, a=math.sqrt(5))

    @property
    def n_tokens(self) -> int:
        return len(self.weight) + (
            0 if self.category_offsets is None else len(self.category_offsets)
        )

    def forward(self, x_num: Tensor, x_cat: ty.Optional[Tensor]) -> Tensor:
        x_some = x_num if x_cat is None else x_cat
        assert x_some is not None

        x_num = torch.cat(
            [torch.ones(len(x_some), self.f, device=x_some.device)]  # [CLS]
            + ([] if x_num is None else [x_num]),
            dim=1,
        )



        x = self.weight[None] * x_num[:, :, None]
        if x_cat is not None:
            x = torch.cat(
                [x, self.category_embeddings(x_cat + self.category_offsets[None])],
                dim=1,
            )
        if self.bias is not None:
            bias = torch.cat(
                [
                    torch.zeros(self.f, self.bias.shape[1], device=x.device),
                    self.bias,
                ]
            )

            x = x + bias[None]
        return x

class Factorizer_row(nn.Module):
    category_offsets: ty.Optional[Tensor]

    def __init__(
            self,
            d_numerical: int,
            categories: ty.Optional[ty.List[int]],
            d_token: int,
            bias: bool,
            f: int,
    ) -> None:
        super().__init__()
        if categories is None:
            d_bias = d_numerical
            self.category_offsets = None
            self.category_embeddings = None
        else:
            d_bias = d_numerical 
            category_offsets = torch.tensor([0] + categories[:-1]).cumsum(0)
            self.register_buffer('category_offsets', category_offsets)
            self.category_embeddings = nn.Embedding(sum(categories), d_token)
            nn_init.kaiming_uniform_(self.category_embeddings.weight, a=math.sqrt(5))
            self.weight_=nn.Parameter(Tensor(f, d_token))
            nn_init.kaiming_uniform_(self.weight_, a=math.sqrt(5))
            self.d = d_token
            print(f'{self.category_embeddings.weight.shape=}')

        # take [CLS] token into account
        self.weight = nn.Parameter(Tensor(d_numerical + f, d_token))
        
        self.bias = nn.Parameter(Tensor(d_bias, d_token)) if bias else None
        # The initialization is inspired by nn.Linear
        nn_init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        
        if self.bias is not None:
            nn_init.kaiming_uniform_(self.bias, a=math.sqrt(5))
        self.f = f
        

    @property
    def n_tokens(self) -> int:
        return len(self.weight) + (
            0 if self.category_offsets is None else len(self.category_offsets)
        )

    def forward(self, x_num: Tensor, x_cat: ty.Optional[Tensor]) -> Tensor:
        x_some = x_num if x_cat is None else x_cat
        assert x_some is not None
        
        x_num = torch.cat(
            [torch.ones(len(x_num), self.f, device=x_some.device)]  # [CLS]
            + ([] if x_num is None else [x_num]),
            dim=1,
        )
        x = self.weight[None] * x_num[:, :, None]
        #print(x_cat)
        
        if x_cat is not None:
            #print(len(x_cat))
            #print(self.category_embeddings(x_cat.permute(1,0) + self.category_offsets[None]).shape)
            x_cat_ = torch.cat(
            [torch.ones((len(x_cat), self.f, self.d), device=x_some.device)*self.weight_]  # [CLS]
            + [(self.category_embeddings(x_cat.permute(1,0) + self.category_offsets[None])).permute(1,0,2)],
            dim=1,
            )
            #print('be x: ', x.shape)
            #8 1 96 + 8 500 96
            #8 501 96
            x = torch.cat(
                [x, x_cat_],
                dim=0,
            )
            #print('af: ',x.shape)#1 96 +50 96
        if self.bias is not None:
            bias = torch.cat(
                [
                    torch.zeros(self.f, self.bias.shape[1], device=x.device),
                    self.bias,
                ]
            )
            #print(bias[None].shape)
            x = x + bias[None]
        return x

class Tokenizer_fi(nn.Module):
    category_offsets: ty.Optional[Tensor]

    def __init__(
            self,
            d_numerical: int,
            categories: ty.Optional[ty.List[int]],
            d_token: int,
            bias: bool,
    ) -> None:
        super().__init__()
        if categories is None:
            d_bias = d_numerical
            self.category_offsets = None
            self.category_embeddings = None
        else:
            d_bias = d_numerical + len(categories)
            category_offsets = torch.tensor([0] + categories[:-1]).cumsum(0)
            self.register_buffer('category_offsets', category_offsets)
            self.category_embeddings = nn.Embedding(sum(categories), d_token)
            nn_init.kaiming_uniform_(self.category_embeddings.weight, a=math.sqrt(5))
            print(f'{self.category_embeddings.weight.shape=}')

        # take [CLS] token into account
        self.weight = nn.Parameter(Tensor(1, d_token))
        
        # The initialization is inspired by nn.Linear
        nn_init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        

    @property
    def n_tokens(self) -> int:
        return len(self.weight) + (
            0 if self.category_offsets is None else len(self.category_offsets)
        )

    def forward(self, x_num: Tensor) -> Tensor:
        x_some = x_num
        assert x_some is not None

        x_num = torch.cat(
            [torch.ones(len(x_some), 1,x_some.shape[2], device=x_some.device)]  # [CLS]
            + ([] if x_num is None else [x_num]),
            dim=1,
        )

        
        x_num[:,:1,:] = self.weight[None] * x_num[:,:1,:].clone()
        
        x = x_num
        """if self.bias is not None:
            bias = torch.cat(
                [
                    torch.zeros(len(x_some), 1, self.bias.shape[1], device=x.device),
                    self.bias,

                    torch.zeros(1, self.bias.shape[1], device=x.device),
                    self.bias,
                ]
            )
            x = x + bias[None]
            x[:,:1,:] = x[:,:1,:] + self.bias"""
            
        return x


class MultiheadAttention(nn.Module):
    def __init__(
            self, d: int, n_heads: int, dropout: float, initialization: str
    ) -> None:
        if n_heads > 1:
            assert d % n_heads == 0
        assert initialization in ['xavier', 'kaiming']

        super().__init__()
        self.W_q = nn.Linear(d, d)
        self.W_k = nn.Linear(d, d)
        self.W_v = nn.Linear(d, d)
        self.W_out = nn.Linear(d, d) if n_heads > 1 else None
        self.n_heads = n_heads
        self.dropout = nn.Dropout(dropout) if dropout else None

        for m in [self.W_q, self.W_k, self.W_v]:
            if initialization == 'xavier' and (n_heads > 1 or m is not self.W_v):
                # gain is needed since W_qkv is represented with 3 separate layers
                nn_init.xavier_uniform_(m.weight, gain=1 / math.sqrt(2))
            nn_init.zeros_(m.bias)
        if self.W_out is not None:
            nn_init.zeros_(self.W_out.bias)

    def _reshape(self, x: Tensor) -> Tensor:
        batch_size, n_tokens, d = x.shape
        d_head = d // self.n_heads
        return (
            x.reshape(batch_size, n_tokens, self.n_heads, d_head)
            .transpose(1, 2)
            .reshape(batch_size * self.n_heads, n_tokens, d_head)
        )

    def forward(
            self,
            x_q: Tensor,
            x_kv: Tensor,
            key_compression: ty.Optional[nn.Linear],
            value_compression: ty.Optional[nn.Linear],
            atype: str
    ) -> Tensor:
        x_q = x_q.to(torch.float32)
        x_kv = x_kv.to(torch.float32)
        x_kv = x_kv.to(torch.float32)
        q, k, v = self.W_q(x_q), self.W_k(x_kv), self.W_v(x_kv)

        #print('1q ' + atype, q.shape)
        #print('1k ' + atype, k.shape)
        #print('1v ' + atype, v.shape)
        for tensor in [q, k, v]:
            assert tensor.shape[-1] % self.n_heads == 0

        if key_compression is not None:
            assert value_compression is not None

            k = key_compression(k.transpose(1, 2)).transpose(1, 2)
            v = value_compression(v.transpose(1, 2)).transpose(1, 2)
        else:
            assert value_compression is None

        batch_size = len(q)
        d_head_key = k.shape[-1] // self.n_heads
        d_head_value = v.shape[-1] // self.n_heads
        n_q_tokens = q.shape[1]
        #print('2q ' + atype, q.shape)
        #print('2k ' + atype, k.shape)
        #print('2v ' + atype, v.shape)

        q = self._reshape(q)
        k = self._reshape(k)
        #print('3q ' + atype, q.shape)
        #print(atype, d_head_key)
        #print(atype, q @ k.transpose(1, 2))
        #print(atype, math.sqrt(d_head_key))

        #print('3k ' + atype, k.shape)
        #print('3v ' + atype, v.shape)

        attention = F.softmax(q @ k.transpose(1, 2) / math.sqrt(d_head_key), dim=-1)
        #print('attention ' + atype, attention.shape)

        if self.dropout is not None:
            attention = self.dropout(attention)
        x = attention @ self._reshape(v)
        #print('1a ' + atype, x.shape)
        x = (
            x.reshape(batch_size, self.n_heads, n_q_tokens, d_head_value)
            .transpose(1, 2)
            .reshape(batch_size, n_q_tokens, self.n_heads * d_head_value)
        )
        #print('2a ' + atype, x.shape)
        if self.W_out is not None:
            x = self.W_out(x)
        #print('3a ' + atype, x.shape)
        return x


class Transformer(nn.Module):
    """Transformer.

    References:
    - https://pytorch.org/docs/stable/generated/torch.nn.Transformer.html
    - https://github.com/facebookresearch/pytext/tree/master/pytext/models/representations/transformer
    - https://github.com/pytorch/fairseq/blob/1bba712622b8ae4efb3eb793a8a40da386fe11d0/examples/linformer/linformer_src/modules/multihead_linear_attention.py#L19
    """





    def __init__(
            self,
            *,
            # tokenizer
            d_numerical: int,
            categories: ty.Optional[ty.List[int]],
            bs: int,
            token_bias: bool,
            # transformer
            n_layers: int,
            d_token: int,
            n_heads: int,
            d_ffn_factor: float,
            attention_dropout: float,
            ffn_dropout: float,
            residual_dropout: float,
            activation: str,
            prenormalization: bool,
            initialization: str,
            # linformer
            kv_compression: ty.Optional[float],
            kv_compression_sharing: ty.Optional[str],
            #
            d_out: int,
            f:int,
            
    ) -> None:
        assert (kv_compression is None) ^ (kv_compression_sharing is not None)

        super().__init__()
        self.factorizer_col = Factorizer_col(d_numerical, categories, d_token, token_bias, f)
        n_tokens = self.factorizer_col.n_tokens

        self.factorizer_row = Factorizer_row(bs, categories, d_token, token_bias, f)
        n_tokens_row = self.factorizer_row.n_tokens

        self.tokenizer_fi = Tokenizer_fi(d_numerical, categories, d_token, token_bias)
        n_tokens_fi = self.factorizer_row.n_tokens

        def make_kv_compression(type):
            assert kv_compression
            if type == 'col':

                compression = nn.Linear(
                    n_tokens, int(n_tokens* kv_compression ), bias=False
                )
            elif type == 'row':

                compression = nn.Linear(
                    n_tokens_row, int(n_tokens_row * kv_compression), bias=False
                )
            else:

                compression = nn.Linear(
                    n_tokens, int((n_tokens)* kv_compression), bias=False
                )
            if initialization == 'xavier':
                nn_init.xavier_uniform_(compression.weight)
            return compression

        self.shared_kv_compression = (
            make_kv_compression()
            if kv_compression and kv_compression_sharing == 'layerwise'
            else None
        )

        def make_normalization():
            return nn.LayerNorm(d_token)

        d_hidden = int(d_token * d_ffn_factor)
        self.layers = nn.ModuleList([])
        for layer_idx in range(n_layers):
            layer = nn.ModuleDict(
                {
                    'attention_col': MultiheadAttention(
                        d_token, n_heads, attention_dropout, initialization
                    ),
                    'linear0_col': nn.Linear(
                        d_token, d_hidden * (2 if activation.endswith('glu') else 1)
                    ),
                    'linear1_col': nn.Linear(d_hidden, d_token),
                    'norm1_col': make_normalization(),
                    'attention_row': MultiheadAttention(
                        d_token, n_heads, attention_dropout, initialization
                    ),
                    'linear0_row': nn.Linear(
                        d_token, d_hidden * (2 if activation.endswith('glu') else 1)
                    ),
                    'linear1_row': nn.Linear(d_hidden, d_token),
                    'norm1_row': make_normalization(),
                    'attention_fi': MultiheadAttention(
                        d_token, n_heads, attention_dropout, initialization
                    ),
                    'linear0_fi': nn.Linear(
                        d_token, d_hidden * (2 if activation.endswith('glu') else 1)
                    ),
                    'linear1_fi': nn.Linear(d_hidden, d_token),
                    'norm1_fi': make_normalization(),

                }
            )
            if not prenormalization or layer_idx:
                layer['norm0_col'] = make_normalization()
                layer['norm0_row'] = make_normalization()
                layer['norm0_fi'] = make_normalization()
            if kv_compression and self.shared_kv_compression is None:
                layer['key_compression'] = make_kv_compression('col')
                layer['key_compression_row'] = make_kv_compression('row')
                layer['key_compression_fi'] = make_kv_compression('fi')
                if kv_compression_sharing == 'headwise':
                    layer['value_compression'] = make_kv_compression('col')
                    layer['value_compression_row'] = make_kv_compression('row')
                    layer['key_compression_fi'] = make_kv_compression('fi')
                else:
                    assert kv_compression_sharing == 'key-value'
            self.layers.append(layer)
        self.combination_layer = nn.Linear(d_numerical, d_token)
        self.activation = lib.get_activation_fn(activation)
        self.last_activation = lib.get_nonglu_activation_fn(activation)
        self.prenormalization = prenormalization
        self.last_normalization = make_normalization() if prenormalization else None
        self.ffn_dropout = ffn_dropout
        self.residual_dropout = residual_dropout
        self.head = nn.Linear(d_token, d_out)
        self.f = f
    def _get_kv_compressions(self, layer):
        return (
            (self.shared_kv_compression, self.shared_kv_compression)
            if self.shared_kv_compression is not None
            else (layer['key_compression'], layer['value_compression'])
            if 'key_compression' in layer and 'value_compression' in layer
            else (layer['key_compression'], layer['key_compression'])
            if 'key_compression' in layer
            else (None, None)
        )

    def _get_kv_compressions_row(self, layer):
        return (
            (self.shared_kv_compression, self.shared_kv_compression)
            if self.shared_kv_compression is not None
            else (layer['key_compression_row'], layer['value_compression_row'])
            if 'key_compression_row' in layer and 'value_compression_row' in layer
            else (layer['key_compression_row'], layer['key_compression_row'])
            if 'key_compression_row' in layer
            else (None, None)
        )
    def _get_kv_compressions_fi(self, layer):
        return (
            (self.shared_kv_compression, self.shared_kv_compression)
            if self.shared_kv_compression is not None
            else (layer['key_compression_fi'], layer['value_compression_fi'])
            if 'key_compression_row' in layer and 'value_compression_fi' in layer
            else (layer['key_compression_fi'], layer['key_compression_fi'])
            if 'key_compression_fi' in layer
            else (None, None)
        )
    def _start_residual(self, x, layer, norm_idx):
        x_residual = x
        x_residual = x_residual.to(torch.float32)

        if self.prenormalization:
            norm_key = f'norm{norm_idx}'
            if norm_key in layer:
                x_residual = layer[norm_key](x_residual)
        return x_residual

    def _end_residual(self, x, x_residual, layer, norm_idx):
        if self.residual_dropout:
            x_residual = F.dropout(x_residual, self.residual_dropout, self.training)
        x = x + x_residual
        if not self.prenormalization:
            x = layer[f'norm{norm_idx}'](x)
        return x

    def forward(self, x_num: Tensor, x_cat: ty.Optional[Tensor]) -> Tensor:
        x = self.factorizer_col(x_num, x_cat)
        if x_cat is not None:
            x_ = self.factorizer_row(x_num.permute(1,0), x_cat.permute(1,0))
        else:
            x_ = self.factorizer_row(x_num.permute(1,0),x_cat)
        for layer_idx, layer in enumerate(self.layers):
            is_last_layer = layer_idx + 1 == len(self.layers)
            layer = ty.cast(ty.Dict[str, nn.Module], layer)


            x_residual = self._start_residual(x, layer, '0_col')
            x_residual = layer['attention_col']((x_residual[:, :self.f] if is_last_layer else x_residual),x_residual,*self._get_kv_compressions(layer), 'col')
            if is_last_layer:
                x = x[:, : x_residual.shape[1]]
            x = self._end_residual(x, x_residual, layer, '0_col')
            x_residual = self._start_residual(x, layer, '1_col')
            x_residual = layer['linear0_col'](x_residual)
            x_residual = self.activation(x_residual)
            if self.ffn_dropout:
                x_residual = F.dropout(x_residual, self.ffn_dropout, self.training)
            x_residual = layer['linear1_col'](x_residual)

            x = self._end_residual(x, x_residual, layer, '1_col')

         
            x_residual = self._start_residual(x_, layer, '0_row')

            x_residual = layer['attention_row'](
                # for the last attention, it is enough to process only [CLS]
                (x_residual[:, :self.f] if is_last_layer else x_residual),
                x_residual,
                *self._get_kv_compressions_row(layer), 'row'
            )
            
            if is_last_layer:
                x_ = x_[:, : x_residual.shape[1]]
            
            x_ = self._end_residual(x_, x_residual, layer, '0_row')
            x_residual = self._start_residual(x_, layer, '1_row')
            x_residual = layer['linear0_row'](x_residual)
            x_residual = self.activation(x_residual)
            if self.ffn_dropout:
                x_residual = F.dropout(x_residual, self.ffn_dropout, self.training)
            x_residual = layer['linear1_row'](x_residual)


            x_ = self._end_residual(x_, x_residual, layer, '1_row')

        x = x.permute(2,0,1)@x_.permute(2,1,0)

        x = x.permute(1,2,0)
        x = self.tokenizer_fi(x)
        x_residual = self._start_residual(x, layer, '0_fi')
        x_residual = layer['attention_fi']((x_residual[:, :1] if is_last_layer else x_residual), x_residual,
                                            *self._get_kv_compressions_fi(layer), 'fi')
        
        x = x[:, : x_residual.shape[1]]
        x = self._end_residual(x, x_residual, layer, '0_fi')
        x_residual = self._start_residual(x, layer, '1_fi')
        x_residual = layer['linear0_fi'](x_residual)
        x_residual = self.activation(x_residual)
        if self.ffn_dropout:
            x_residual = F.dropout(x_residual, self.ffn_dropout, self.training)
        x_residual = layer['linear1_fi'](x_residual)

        x = self._end_residual(x, x_residual, layer, '1_fi')


        assert x.shape[1] == 1
        x = x[:, 0]
        x = x.to(torch.float32)
        if self.last_normalization is not None:
            x = self.last_normalization(x)
        x = self.last_activation(x)
        x = self.head(x)
        x = x.squeeze(-1)
        return x


# %%
if __name__ == "__main__":
    args, output = lib.load_config()
   
    args['model'].setdefault('token_bias', True)
    args['model'].setdefault('kv_compression', None)
    args['model'].setdefault('kv_compression_sharing', None)

    # %%
    zero.set_randomness(args['seed'])
    dataset_dir = lib.get_path(args['data']['path'])
    print(dataset_dir)
    stats: ty.Dict[str, ty.Any] = {
        'dataset': dataset_dir.name,
        'algorithm': Path(__file__).stem,
        **lib.load_json(output / 'stats.json'),
    }
    timer = zero.Timer()
    timer.run()

    D = lib.Dataset.from_dir(dataset_dir)
    X = D.build_X(
        normalization=args['data'].get('normalization'),
        num_nan_policy='mean',
        cat_nan_policy='new',
        cat_policy=args['data'].get('cat_policy', 'indices'),
        cat_min_frequency=args['data'].get('cat_min_frequency', 0.0),
        seed=args['seed'],
    )
    if not isinstance(X, tuple):
        X = (X, None)
    zero.set_randomness(args['seed'])
    Y, y_info = D.build_y(args['data'].get('y_policy'))
    lib.dump_pickle(y_info, output / 'y_info.pickle')
    X = tuple(None if x is None else lib.to_tensors(x) for x in X)
    Y = lib.to_tensors(Y)
    device = lib.get_device()
    if device.type != 'cpu':
        X = tuple(
            None if x is None else {k: v.to(device) for k, v in x.items()} for x in X
        )
        Y_device = {k: v.to(device) for k, v in Y.items()}
    else:
        Y_device = Y
    X_num, X_cat = X
    
    del X
    if not D.is_multiclass:
        Y_device = {k: v.float() for k, v in Y_device.items()}

    train_size = D.size(lib.TRAIN)
    batch_size = args['training']['batch_size']
    epoch_size = stats['epoch_size'] = math.ceil(train_size / batch_size)
    eval_batch_size = args['training']['eval_batch_size']
    chunk_size = None

    loss_fn = (
        F.binary_cross_entropy_with_logits
        if D.is_binclass
        else F.cross_entropy
        if D.is_multiclass
        else F.mse_loss
    )
    model = Transformer(
        d_numerical=0 if X_num is None else X_num['train'].shape[1],
        categories=lib.get_categories(X_cat),
        d_out=D.info['n_classes'] if D.is_multiclass else 1, 
        bs=args['training']['batch_size'],
        **args['model']
    ).to(device)
    if torch.cuda.device_count() > 1:  # type: ignore[code]
        print('Using nn.DataParallel')
        model = nn.DataParallel(model)
    stats['n_parameters'] = lib.get_n_parameters(model)


    def needs_wd(name):
        return all(x not in name for x in ['factorizer','tokenizer', '.norm', '.bias'])


    for x in ['factorizer','tokenizer', '.norm', '.bias']:
        assert any(x in a for a in (b[0] for b in model.named_parameters()))
    parameters_with_wd = [v for k, v in model.named_parameters() if needs_wd(k)]
    parameters_without_wd = [v for k, v in model.named_parameters() if not needs_wd(k)]
    optimizer = lib.make_optimizer(
        args['training']['optimizer'],
        (
            [
                {'params': parameters_with_wd},
                {'params': parameters_without_wd, 'weight_decay': 0.0},
            ]
        ),
        args['training']['lr'],
        args['training']['weight_decay'],
    )

    stream = zero.Stream(lib.IndexLoader(train_size, batch_size, True, device))
    progress = zero.ProgressTracker(args['training']['patience'])
    training_log = {lib.TRAIN: [], lib.VAL: [], lib.TEST: []}
    timer = zero.Timer()
    checkpoint_path = output / 'checkpoint.pt'


    def print_epoch_info():
        print(f'\n>>> Epoch {stream.epoch} | {lib.format_seconds(timer())} | {output}')
        print(
            ' | '.join(
                f'{k} = {v}'
                for k, v in {
                    'lr': lib.get_lr(optimizer),
                    'batch_size': batch_size,
                    'chunk_size': chunk_size,
                    'epoch_size': stats['epoch_size'],
                    'n_parameters': stats['n_parameters'],
                }.items()
            )
        )


    def apply_model(part, idx):
        return model(
            None if X_num is None else X_num[part][idx],
            None if X_cat is None else X_cat[part][idx],
        )


    @torch.no_grad()
    def evaluate(parts):
        global eval_batch_size
        model.eval()
        metrics = {}
        predictions = {}
        for part in parts:
            while eval_batch_size:
                try:
                    predictions[part] = (
                        torch.cat(
                            [
                                apply_model(part, idx)
                                for idx in lib.IndexLoader(
                                D.size(part), eval_batch_size, False, device
                            )
                            ]
                        )
                        .cpu()
                        .numpy()
                    )
                except RuntimeError as err:
                    if not lib.is_oom_exception(err):
                        raise
                    eval_batch_size //= 2
                    print('New eval batch size:', eval_batch_size)
                    stats['eval_batch_size'] = eval_batch_size
                else:
                    break
            if not eval_batch_size:
                RuntimeError('Not enough memory even for eval_batch_size=1')
            metrics[part] = lib.calculate_metrics(
                D.info['task_type'],
                Y[part].numpy(),  # type: ignore[code]
                predictions[part],  # type: ignore[code]
                'logits',
                y_info,
            )
        for part, part_metrics in metrics.items():
            print(f'[{part:<5}]', lib.make_summary(part_metrics))
        return metrics, predictions


    def save_checkpoint(final):
        torch.save(
            {
                'model': model.state_dict(),
                'optimizer': optimizer.state_dict(),
                'stream': stream.state_dict(),
                'random_state': zero.get_random_state(),
                **{
                    x: globals()[x]
                    for x in [
                        'progress',
                        'stats',
                        'timer',
                        'training_log',
                    ]
                },
            },
            checkpoint_path,
        )
        lib.dump_stats(stats, output, final)
        lib.backup_output(output)


    # %%
    timer.run()
    for epoch in stream.epochs(args['training']['n_epochs']):
        print_epoch_info()

        model.train()
        epoch_losses = []
        for batch_idx in epoch:
            loss, new_chunk_size = lib.train_with_auto_virtual_batch(
                optimizer,
                loss_fn,
                lambda x: (apply_model(lib.TRAIN, x), Y_device[lib.TRAIN][x]),
                batch_idx,
                chunk_size or batch_size,
            )
            epoch_losses.append(loss.detach())
            if new_chunk_size and new_chunk_size < (chunk_size or batch_size):
                stats['chunk_size'] = chunk_size = new_chunk_size
                print('New chunk size:', chunk_size)
        epoch_losses = torch.stack(epoch_losses).tolist()
        training_log[lib.TRAIN].extend(epoch_losses)
        print(f'[{lib.TRAIN}] loss = {round(sum(epoch_losses) / len(epoch_losses), 3)}')

        metrics, predictions = evaluate([lib.VAL, lib.TEST])
        for k, v in metrics.items():
            training_log[k].append(v)
        progress.update(metrics[lib.VAL]['score'])

        if progress.success:
            print('New best epoch!')
            stats['best_epoch'] = stream.epoch
            stats['metrics'] = metrics
            save_checkpoint(False)
            for k, v in predictions.items():
                np.save(output / f'p_{k}.npy', v)

        elif progress.fail:
            break

    # %%
    print('\nRunning the final evaluation...')
    model.load_state_dict(torch.load(checkpoint_path)['model'])
    stats['metrics'], predictions = evaluate(lib.PARTS)
    for k, v in predictions.items():
        np.save(output / f'p_{k}.npy', v)
    stats['time'] = lib.format_seconds(timer())
    save_checkpoint(True)
    print('Done!')
