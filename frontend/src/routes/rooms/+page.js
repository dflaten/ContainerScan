export async function load({ parent }) {
  const parentData = await parent();

  return {
    rooms: parentData.rooms,
    tags: parentData.tags,
    colors: parentData.colors
  };
}
