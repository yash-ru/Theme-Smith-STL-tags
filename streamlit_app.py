import streamlit as st
import re

# Page config
st.set_page_config(
    page_title="STL Tags Converter",
    layout="wide"
)

# Mapping from old tag names/types to new theme_prop names
TAG_MAPPING = {
    'CMResultsAdUrl_font-size': 'ad_url_font_size',
    'CMResultsAdUrl_color': 'ad_url_font_color',
    'CMResultsAdUrl_font-family': 'ad_url_font_family',  # Fixed: hyphen -> underscore
    'CMResultsAdTitle_font-size': 'ad_title_font_size',
    'CMResultsAdTitle_color': 'ad_title_color',
    'CMResultsAdTitle_font-family': 'ad_title_font_family',
    'CMResultsAdDescription_font-size': 'ad_desc_font_size',
    'CMResultsAdDescription_color': 'ad_desc_font_color',
    'CMResultsAdDescription_font-family': 'ad_desc_font_family',
    'ResultsAdDescription_font-size': 'ad_desc_desktop_font_size',
    'CustomResultsAdUrlBackGround_color': 'ad_background',
    'CustomResultsAdUrlBorder_color': 'ad_border_color',
    'CMContentArea_color': 'body_background',
    'HeaderArea_color': 'header_background',
    'AdBorder_color': 'cta_border_color',
    'CMAdsLabel_color': 'cta_background',
    'Bullet_font-size': 'cta_text_font_size',
    'BulletText_color': 'cta_text_font_color',
    'BulletShape_color': 'chevron_color',
    'KeywordsHoverUnderline_checkbox': 'title_hover_underline',
    'KeywordArea_color': 'keyword_link_color',
    'relcontspan_font-family': 'relcont_span_font_family',
    'HeaderText_font-size': 'header_text_font_size',
    'HeaderText_color': 'header_text_color',
    'HeaderText_textCase': 'header_text_case',
    'HeaderText_tallness': 'header_border_width',
    'HeaderText_border-style': 'header_border_style',
    'CMResultsAdUrl_font-size_desktop': 'ad_url_desktop_font_size',
    'CMResultsAdTitle_font-size_desktop': 'ad_title_desktop_font_size',
    'AdBorder_color_desktop': 'cta_border_desktop_color',
    'InnerBorder_color': 'ad_url_font_color',
    'CallToAction_content': 'cta_text'
}

def convert_tag(match, name, value, type):
    """Convert old tag format to new theme_prop format"""
    key = f"{name}_{type}"
    new_prop_name = TAG_MAPPING.get(key)
    
    # If no mapping found, create a default name
    if not new_prop_name:
        # Convert CamelCase to snake_case
        new_prop_name = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_').replace('__', '_') + '_' + type.lower()
    
    return f'<tag:theme_prop:{new_prop_name} default="{value}" />'

def get_context_suffix(context_before, css_property=None):
    """Get context suffix based on surrounding code"""
    suffix = ""
    
    # Check if inside media query (desktop)
    if '@media' in context_before:
        # Find the last @media before this tag
        media_pos = context_before.rfind('@media')
        if media_pos != -1:
            # Check if there's a closing brace after @media (meaning we're still inside)
            after_media = context_before[media_pos:]
            open_braces = after_media.count('{')
            close_braces = after_media.count('}')
            if open_braces > close_braces:
                suffix = "_desktop"
                return suffix  # Desktop takes priority
    
    # Check CSS property context
    if css_property:
        css_prop_lower = css_property.lower()
        if 'border' in css_prop_lower and 'color' in css_prop_lower:
            suffix = "_border"
            return suffix  # Border color takes priority
    
    # Check selector context (more specific selectors first)
    selector_match = re.search(r'\.([a-z-]+)\s*\{[^}]*$', context_before)
    if selector_match:
        selector = selector_match.group(1)
        if 'arrow-text' in selector:
            suffix = "_cta_text"
        elif 'arrow' in selector or 'cta' in selector:
            suffix = "_cta"
        elif 'title' in selector and 'arrow' not in selector:
            suffix = "_title"
    
    return suffix

def find_duplicate_props(output):
    """Find all prop names that appear more than once"""
    prop_pattern = r'<tag:theme_prop:([^>\s]+)\s+default=["\']([^"\']*)["\']\s*/>'
    matches = list(re.finditer(prop_pattern, output))
    
    # Group by prop name
    prop_groups = {}
    for match in matches:
        prop_name = match.group(1)
        if prop_name not in prop_groups:
            prop_groups[prop_name] = []
        prop_groups[prop_name].append({
            'match': match,
            'value': match.group(2),
            'position': match.start(),
            'full_match': match.group(0)
        })
    
    # Return only duplicates (appears more than once)
    duplicates = {name: occurrences for name, occurrences in prop_groups.items() 
                 if len(occurrences) > 1}
    
    return duplicates

def rename_duplicates(output, original_html):
    """Rename duplicate prop names with context suffixes"""
    duplicates = find_duplicate_props(output)
    
    if not duplicates:
        return output
    
    # Find all original tags in order
    original_tags = []
    for match in re.finditer(r'<tagd:style\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s+type=["\']([^"\']+)["\']\s*/>', original_html, re.IGNORECASE):
        original_tags.append({
            'match': match,
            'name': match.group(1),
            'value': match.group(2),
            'type': match.group(3),
            'position': match.start()
        })
    for match in re.finditer(r'<tagd:style\s+type=["\']([^"\']+)["\']\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s*/>', original_html, re.IGNORECASE):
        original_tags.append({
            'match': match,
            'name': match.group(2),
            'value': match.group(3),
            'type': match.group(1),
            'position': match.start()
        })
    original_tags.sort(key=lambda x: x['position'])
    
    # Find all converted tags in order
    converted_tags = []
    for match in re.finditer(r'<tag:theme_prop:([^>\s]+)\s+default=["\']([^"\']*)["\']\s*/>', output):
        converted_tags.append({
            'match': match,
            'prop_name': match.group(1),
            'value': match.group(2),
            'position': match.start()
        })
    converted_tags.sort(key=lambda x: x['position'])
    
    # Match converted tags to original tags by position order
    # Process duplicates in reverse order to maintain positions
    all_replacements = []
    for prop_name, occurrences in duplicates.items():
        # Keep first occurrence, rename others
        for i, occ in enumerate(occurrences):
            if i == 0:
                continue  # Keep first one
            
            # Find this occurrence in converted_tags list
            occ_index = None
            for idx, conv_tag in enumerate(converted_tags):
                if conv_tag['position'] == occ['position']:
                    occ_index = idx
                    break
            
            if occ_index is not None and occ_index < len(original_tags):
                # Get corresponding original tag
                orig_tag = original_tags[occ_index]
                context_start = max(0, orig_tag['position'] - 1000)
                context_before = original_html[context_start:orig_tag['position']]
            else:
                # Fallback: use converted output context
                context_start = max(0, occ['position'] - 1000)
                context_before = output[context_start:occ['position']]
            
            # Extract CSS property from original HTML
            css_prop_match = re.search(r'([a-z-]+):\s*<tagd:style', context_before[-300:], re.IGNORECASE)
            css_property = css_prop_match.group(1) if css_prop_match else None
            
            # Get context suffix
            suffix = get_context_suffix(context_before, css_property)
            
            # If no suffix found, use index as fallback
            if not suffix:
                suffix = f"_{i}"
            
            # Create new prop name
            new_prop_name = prop_name + suffix
            
            # Replace this occurrence
            old_tag = occ['full_match']
            new_tag = old_tag.replace(f'<tag:theme_prop:{prop_name}', f'<tag:theme_prop:{new_prop_name}')
            all_replacements.append((occ['position'], old_tag, new_tag))
    
    # Sort by position (reverse order) and replace
    all_replacements.sort(key=lambda x: x[0], reverse=True)
    for position, old_tag, new_tag in all_replacements:
        output = output[:position] + new_tag + output[position + len(old_tag):]
    
    return output

def convert_tags(input_html):
    """Main conversion function with two-pass approach"""
    if not input_html or not input_html.strip():
        return ""
    
    original_html = input_html  # Keep original for context detection
    output = input_html
    
    # PASS 1: Convert <tagd:style name="..." value="..." type="..." /> to <tag:theme_prop:... default="..." />
    output = re.sub(
        r'<tagd:style\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s+type=["\']([^"\']+)["\']\s*/>',
        lambda m: convert_tag(m.group(0), m.group(1), m.group(2), m.group(3)),
        output,
        flags=re.IGNORECASE
    )
    
    # Also handle tags with different attribute order
    output = re.sub(
        r'<tagd:style\s+type=["\']([^"\']+)["\']\s+name=["\']([^"\']+)["\']\s+value=["\']([^"\']*)["\']\s*/>',
        lambda m: convert_tag(m.group(0), m.group(2), m.group(3), m.group(1)),
        output,
        flags=re.IGNORECASE
    )
    
    # PASS 2: Find and rename duplicates with context suffixes
    output = rename_duplicates(output, original_html)
    
    # Clean up: ensure tags don't have excessive line breaks around them
    output = re.sub(r'\s*\n\s*(<tag:[^>]+>)\s*\n\s*', r' \1 ', output)
    output = re.sub(r'(<tag:[^>]+>)\s*\n\s*', r'\1 ', output)
    
    return output

# UI
st.title("STL Tags Converter")
st.markdown("**Convert Old Framework Tags to New Framework Format**")
st.markdown("---")

# Create two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("Old Framework (Input)")
    
    input_text = st.text_area(
        "Paste your old framework HTML here:",
        value="",
        height=600,
        key="input",
        label_visibility="collapsed"
    )
    
    # Convert button
    st.button("Convert", key="convert", use_container_width=True)

with col2:
    st.subheader("New Framework (Output)")
    
    # Always convert when there's input
    output_text = ""
    if input_text and input_text.strip():
        output_text = convert_tags(input_text)
    
    # Display output textarea - use dynamic key based on input hash to force updates
    input_hash = hash(input_text) if input_text else 0
    st.text_area(
        "Converted HTML:",
        value=output_text,
        height=600,
        key=f"output_{input_hash}",
        label_visibility="collapsed",
        placeholder="Converted HTML will appear here..."
    )

# Footer
st.markdown("---")
st.caption("Made with Streamlit")
