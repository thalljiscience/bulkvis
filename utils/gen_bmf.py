import pandas as pd
import numpy as np
from argparse import ArgumentParser
from pathlib import Path
import warnings


def main():
    """Main method, converting and exporting PAF + SS to BMF"""
    warnings.warn('This is temporary and will be removed without notice')
    # Get arguments
    args = get_args()
    paf_path = args.paf
    # Open [PAF] mapping file with specified columns
    col_names = ['Qname', 'Strand', 'Tname', 'Tstart', 'Tend', 'block_length', 'alignment_type']
    pf = pd.read_csv(paf_path, sep='\t', header=None, names=col_names, usecols=[0, 4, 5, 7, 8, 10, 12])
    # Thin PAF file by 'Primary alignment type' and drop duplicates
    pf = pf[pf['alignment_type'] == 'tp:A:P']
    pf = pf.sort_values(['Qname', 'Tname', 'block_length'], ascending=[True, True, False])
    pf = pf.drop_duplicates(['Qname', 'Tname'], keep='first')
    # Open sequencing_summary.txt file 
    cols = ['read_id', 'run_id', 'channel', 'start_time', 'duration']
    ss = pd.read_csv(args.summary, sep='\t', usecols=cols)
    # Merge seq_sum and paf files 
    df = pd.merge(ss, pf, left_on='read_id', right_on='Qname', how='outer')
    df = df.dropna()
    
    df['end_time'] = df['start_time'] + df['duration']
    df['start_mapping'] = df[['Tstart', 'Tend']].min(axis=1).astype('int64').map('{0:,d}'.format)
    df['end_mapping'] = df[['Tstart', 'Tend']].max(axis=1).astype('int64').map('{0:,d}'.format)
    # df['start_mapping'] = np.where(df['Strand'] == '+',
    #                                df[['Tstart', 'Tend']].min(axis=1),
    #                                df[['Tstart', 'Tend']].min(axis=1)
    #                                )
    # df['end_mapping'] = np.where(df['Strand'] == '+',
    #                              df[['Tstart', 'Tend']].max(axis=1),
    #                              df[['Tstart', 'Tend']].max(axis=1)
    #                              )
    # df['sm'] = df['start_mapping'].astype('int64').map('{0:,d}'.format)
    # df['em'] = df['end_mapping'].astype('int64').map('{0:,d}'.format)
    df['label'] = (df['Tname'].astype('str') + ": " +
                   df['start_mapping'].astype('str') + " - " +
                   df['end_mapping'].astype('str')
                   )

    df = df.rename(columns={'Tname': 'target_name', 'Strand': 'strand'})
    # export as <run_id>.bmf
    header = ['run_id', 'read_id', 'channel', 'start_time',
              'end_time', 'target_name', 'strand',
              'start_mapping', 'end_mapping', 'label']
    i = 0
    for k, v in df.groupby(['run_id']):
        # Join 'bmf' path, run_id, and file extension
        p = Path(args.bmf).joinpath(str(k) + '.bmf')
        v.to_csv(p, sep="\t", header=True, columns=header, index=False)
        i += 1

    print('{n} files written to {p}'.format(n=i, p=args.bmf))


def full_path(file):
    return str(Path(file).expanduser().resolve())


def get_args():
    parser = ArgumentParser(
        description="""Parse sequencing_summary.txt files 
                       and .paf files to format mapping info for bulkvis""",
        add_help=False)
    general = parser.add_argument_group(
        title='General options')
    general.add_argument("-h", "--help",
                         action="help",
                         help="Show this help and exit"
                         )
    in_args = parser.add_argument_group(
        title='Input sources'
    )
    in_args.add_argument("-s", "--summary",
                         help="A sequencing summary file generated by albacore",
                         type=full_path,
                         default="",
                         required=True,
                         metavar=''
                         )
    in_args.add_argument("-p", "--paf",
                         help="A paf file generated by minimap2",
                         type=full_path,
                         default='',
                         required=True,
                         metavar=''
                         )
    out_args = parser.add_argument_group(
            title='Output:'
    )
    out_args.add_argument('--bmf',
                          help='''Specify the output folder, where files will be written as <run_id>.bmf. This 
                                  should be the \'map\' path specified in the config.ini''',
                          type=full_path,
                          metavar='',
                          required=True
                          )
    return parser.parse_args()


if __name__ == '__main__':
    main()

