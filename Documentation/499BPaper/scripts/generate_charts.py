#!/usr/bin/env python3
"""
Chart generation script for AIris research paper.
Generates visualization charts for the Results section.
"""

import matplotlib.pyplot as plt
import numpy as np
import os

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAMS_DIR = os.path.join(SCRIPT_DIR, '..', 'diagrams')

# Ensure diagrams directory exists
os.makedirs(DIAGRAMS_DIR, exist_ok=True)


def generate_latency_comparison():
    """
    Generate a bar chart comparing early prototype latency vs current system.
    
    Data sources:
    - Early Prototype (Aug 2025): 14.09s from EvaluationReport.md
    - Current System: 340ms from Table 7.1
    """
    # Data
    systems = ['Early Prototype\n(Aug 2025)', 'Current System\n(Jan 2026)']
    latencies = [14090, 340]  # in ms
    
    # Create figure with clean styling
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Bar chart with AIris-inspired colors
    colors = ['#C75050', '#5A9E6F']  # Red for old, Green for new
    bars = ax.bar(systems, latencies, color=colors, width=0.5, edgecolor='#333333', linewidth=1.5)
    
    # Add value labels on top of bars
    for bar, val in zip(bars, latencies):
        height = bar.get_height()
        if val > 1000:
            label = f'{val/1000:.2f}s'
        else:
            label = f'{val}ms'
        ax.text(bar.get_x() + bar.get_width()/2., height + 300,
                label, ha='center', va='bottom', fontsize=14, fontweight='bold', color='#333333')
    
    # Add real-time threshold line (2 seconds)
    ax.axhline(y=2000, color='#C9AC78', linestyle='--', linewidth=2.5, 
               label='Real-time Threshold (2000ms)')
    
    # Styling
    ax.set_ylabel('Latency (ms)', fontsize=12, fontweight='bold')
    ax.set_title('Latency Improvement: Early Prototype vs Current System', 
                 fontsize=14, fontweight='bold', pad=15)
    ax.set_ylim(0, 16000)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='-', linewidth=0.5)
    
    # Remove top and right spines for cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.5)
    ax.spines['bottom'].set_linewidth(1.5)
    
    # Add improvement annotation with arrow
    ax.annotate('41x\nFaster', 
                xy=(1, 500), 
                xytext=(0.5, 7500),
                fontsize=18, fontweight='bold', color='#5A9E6F',
                arrowprops=dict(arrowstyle='->', color='#5A9E6F', lw=2.5),
                ha='center', va='center')
    
    plt.tight_layout()
    
    # Save to diagrams folder
    output_path = os.path.join(DIAGRAMS_DIR, 'latency_comparison.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
    print(f"✓ Generated: {output_path}")
    
    plt.close()
    return output_path


def main():
    """Generate all charts for the paper."""
    print("Generating charts for AIris research paper...")
    print("-" * 50)
    
    # Generate latency comparison chart
    generate_latency_comparison()
    
    print("-" * 50)
    print("All charts generated successfully!")


if __name__ == "__main__":
    main()
